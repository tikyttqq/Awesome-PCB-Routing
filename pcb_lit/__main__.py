from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from .core import catalog_category, classify, contains_han, read_json, same_paper, unique, upsert, validate, write_json
from .http import Client, FetchError
from .render import render
from .sources import arxiv_refresh, arxiv_search, crossref_search, s2_neighbors

ROOT = Path(__file__).resolve().parent.parent


def collect(args, root, papers, config, edges):
    since = args.since or (date.today() - timedelta(days=args.days)).isoformat()
    date.fromisoformat(since)
    client = Client(root / ".cache/http", os.getenv("CONTACT_EMAIL", ""), ttl=0 if args.no_cache else 21600)
    report = {"since": since, "successful_jobs": 0, "received": 0, "new_candidates": 0, "filtered": 0,
              "filtered_non_english": 0,
              "warnings": [], "sources": args.sources, "graph": args.graph}

    def consume(name, stream, seed=None, direction=None):
        try:
            for p in stream:
                report["received"] += 1
                if contains_han(p):
                    report["filtered_non_english"] += 1
                    continue
                relevant = classify(p, config)
                existing = any(same_paper(old, p) for old in papers)
                if not (relevant or existing):
                    report["filtered"] += 1
                    continue
                merged, added = upsert(papers, p)
                classify(merged, config)
                report["new_candidates"] += int(added)
                if seed and merged["id"] != seed["id"]:
                    citing, cited = (seed["id"], merged["id"]) if direction == "references" else (merged["id"], seed["id"])
                    edges.append({"citing": citing, "cited": cited, "source": "semantic_scholar"})
            report["successful_jobs"] += 1
        except (FetchError, KeyError, ValueError, TypeError) as exc:
            # FetchError is sanitized by the HTTP layer; never print authenticated URLs.
            warning = f"{name}: {exc}" if isinstance(exc, FetchError) else f"{name}: malformed metadata ({type(exc).__name__})"
            report["warnings"].append(warning)
            print("WARNING: " + warning, file=sys.stderr)

    if "arxiv" in args.sources:
        consume("arxiv search", arxiv_search(client, config["arxiv_query"], since, args.max_pages))
        ids = sorted({i for p in papers if p["status"] == "approved" for i in p["identifiers"].get("arxiv", [])})
        if ids:
            consume("arxiv refresh", arxiv_refresh(client, ids))
    if "crossref" in args.sources:
        for query in config["crossref_queries"]:
            consume("crossref " + query, crossref_search(client, query, since, os.getenv("CONTACT_EMAIL", ""), args.max_pages))
    if args.graph:
        seed_ids = set(args.seed or [p["id"] for p in papers if p["status"] == "approved"])
        unknown = seed_ids - {p["id"] for p in papers}
        if unknown:
            raise ValueError("Unknown graph seeds: " + ", ".join(sorted(unknown)))
        # Snapshot prevents recursively expanding newly found nodes in this run.
        seeds = [p for p in papers if p["id"] in seed_ids and p["status"] != "rejected"]
        for seed in seeds:
            for direction in ("references", "citations"):
                consume("graph " + seed["id"] + "/" + direction,
                        s2_neighbors(client, seed, direction, os.getenv("S2_API_KEY", ""), args.max_pages), seed, direction)
    edges[:] = unique(edges)
    validate(papers, config, edges)
    save(root, papers, edges)
    render(root, papers, config)
    write_json(root / ".reports/latest.json", report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 2 if not report["successful_jobs"] or (report["warnings"] and not args.allow_partial) else 0


def save(root, papers, edges):
    write_json(root / "data/papers.json", sorted(papers, key=lambda p: p["id"]))
    write_json(root / "data/relations.json", sorted(edges, key=lambda e: (e["citing"], e["cited"], e["source"])))


def main(argv=None):
    parser = argparse.ArgumentParser(description="PCB literature catalog: discover → review → render")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository/data root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Check metadata, taxonomy and duplicate identities offline")
    sub.add_parser("render", help="Regenerate Markdown, CSV and BibTeX offline")
    crawl = sub.add_parser("collect", help="Query official scholarly APIs")
    crawl.add_argument("--sources", nargs="+", choices=["arxiv", "crossref"], default=["arxiv", "crossref"])
    crawl.add_argument("--days", type=int, default=28)
    crawl.add_argument("--since", help="YYYY-MM-DD, inclusive; overrides --days")
    crawl.add_argument("--max-pages", type=int, default=5)
    crawl.add_argument("--graph", action="store_true", help="Expand one-hop references and citing papers using Semantic Scholar")
    crawl.add_argument("--seed", action="append", help="Graph seed record id, repeatable; defaults to approved records")
    crawl.add_argument("--no-cache", action="store_true")
    crawl.add_argument("--allow-partial", action="store_true", help="Exit 0 on partial source failures; report still records warnings")
    review = sub.add_parser("review", help="Approve/reject one candidate after checking its sources")
    review.add_argument("id")
    review.add_argument("decision", choices=["approved", "rejected"])
    review.add_argument("--summary", help="Human-written reading note; required on approval")
    review.add_argument("--tasks", nargs="+", help="Override suggested task labels")
    review.add_argument("--category", choices=["surveys", "routing", "other"], help="Single primary display category")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    config = read_json(root / "config.json")
    papers, edges = read_json(root / "data/papers.json", []), read_json(root / "data/relations.json", [])
    validate(papers, config, edges)
    if args.command == "collect":
        if args.days < 1 or args.max_pages < 1:
            parser.error("--days and --max-pages must be positive")
        return collect(args, root, papers, config, edges)
    if args.command == "review":
        p = next((p for p in papers if p["id"] == args.id), None)
        if p is None:
            parser.error("Unknown paper id: " + args.id)
        if args.decision == "approved":
            if not args.summary or not args.summary.strip():
                parser.error("Approval requires --summary after reading the source")
            p.update(summary=args.summary.strip(), summary_kind="human")
        p["status"] = args.decision
        if args.tasks:
            p["tasks"] = args.tasks
        p["category"] = args.category or catalog_category(p)
        validate(papers, config, edges)
        save(root, papers, edges)
    if args.command in ("render", "review"):
        render(root, papers, config)
    print(f"{args.command}: OK ({len(papers)} records)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
