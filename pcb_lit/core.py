from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path


def clean(value: str | None) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def contains_han(value) -> bool:
    """Keep repository prose and imported metadata free of CJK ideographs."""
    if isinstance(value, str):
        return bool(re.search(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]", value))
    if isinstance(value, dict):
        return any(contains_han(k) or contains_han(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(contains_han(v) for v in value)
    return False


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in value if c.isalnum())


def doi(value: str) -> str:
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value.strip(), flags=re.I).lower()


def arxiv_id(value: str) -> str:
    value = re.sub(r"^.*arxiv\.org/(?:abs|pdf)/", "", value.strip(), flags=re.I)
    return re.sub(r"v\d+$", "", value.removesuffix(".pdf"))


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)


def write_json(path: Path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def unique(items):
    seen, result = set(), []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def record(title, authors, year, url, provider, *, abstract="", identifiers=None, **extra):
    return dict(
        id="p-" + hashlib.sha256(normalized(title).encode()).hexdigest()[:12],
        title=clean(title), authors=authors, year=year, url=url,
        abstract=clean(abstract), identifiers=identifiers or {},
        venue="", venue_verified=False, publication_type="unknown",
        tasks=[], methods=[], status="candidate", summary="", summary_kind="none",
        sources=[{"provider": provider, "url": url}], **extra,
    )


def same_paper(a, b):
    for kind in set(a["identifiers"]) & set(b["identifiers"]):
        if set(a["identifiers"][kind]) & set(b["identifiers"][kind]):
            return True
    # Exact title + shared author + nearby year only. Never fuzzy-merge Part I/II.
    if normalized(a["title"]) != normalized(b["title"]):
        return False
    if a.get("year") and b.get("year") and abs(a["year"] - b["year"]) > 2:
        return False
    names_a = {normalized(n) for n in a.get("authors", [])}
    names_b = {normalized(n) for n in b.get("authors", [])}
    return bool(names_a & names_b)


def merge_record(old, incoming):
    for kind, values in incoming["identifiers"].items():
        old["identifiers"][kind] = sorted(set(old["identifiers"].get(kind, [])) | set(values))
    old["sources"] = unique(old.get("sources", []) + incoming.get("sources", []))
    if old["status"] == "approved":
        changes = {key: incoming[key] for key in ("title", "venue", "year")
                   if incoming.get(key) and old.get(key) and incoming[key] != old[key]}
        if changes:
            provider = incoming["sources"][0]["provider"]
            old.setdefault("metadata_suggestions", {})[provider] = changes
    # Preserve editorial decisions, including rejected records and approved metadata.
    for key in ("title", "authors", "year", "url", "abstract", "venue"):
        if not old.get(key) and incoming.get(key):
            old[key] = incoming[key]
    if old["status"] == "candidate":
        if len(incoming.get("abstract", "")) > len(old.get("abstract", "")):
            old["abstract"] = incoming["abstract"]
        if incoming.get("arxiv_updated", "") > old.get("arxiv_updated", ""):
            for key in ("title", "abstract", "arxiv_updated", "arxiv_version", "journal_ref"):
                if key in incoming:
                    old[key] = incoming[key]
        if old.get("publication_type") == "unknown":
            old["publication_type"] = incoming.get("publication_type", "unknown")
    return old


def upsert(papers, incoming):
    matches = [p for p in papers if same_paper(p, incoming)]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous duplicate: {incoming['title']}; merge records manually")
    if matches:
        return merge_record(matches[0], incoming), False
    incoming.setdefault("discovered_on", date.today().isoformat())
    papers.append(incoming)
    return incoming, True


def catalog_category(paper):
    """One primary display category; task and method tags remain independent."""
    if paper.get("category"):
        return paper["category"]
    title = paper["title"].lower()
    if re.search(r"\bsurveys?\b|\breviews?\b|\boverview\b", title):
        return "surveys"
    if re.search(r"schematic|placement|migration|migrator", title) and not re.search(r"routing|autorout|escape|fanout", title):
        return "other"
    if re.search(r"routing|autorout|escape|fanout|fan-out|path connections", title) or "routing" in paper.get("tasks", []):
        return "routing"
    return "other"


def classify(paper, config):
    title = paper["title"].lower()
    text = title + " " + paper.get("abstract", "").lower()
    board = bool(re.search(config["scope"]["board_regex"], text))
    design = bool(re.search(config["scope"]["design_regex"], text))
    excluded = bool(re.search(config["scope"]["exclude_title_regex"], title))
    tasks = [k for k, v in config["tasks"].items() if re.search(v["regex"], text)]
    methods = [k for k, v in config["methods"].items() if re.search(v["regex"], text)]
    paper["classification"] = {
        "relevant": board and design and not excluded,
        "board_context": board, "design_context": design, "excluded_title": excluded,
        "suggested_tasks": tasks, "suggested_methods": methods,
        "rule_version": config["rule_version"],
    }
    if paper["status"] == "candidate":
        paper["tasks"], paper["methods"] = tasks, methods
        paper["category"] = catalog_category(paper)
        # An explicitly labelled excerpt, never an invented claim about results.
        if paper.get("abstract"):
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", paper["abstract"])
            paper["summary"] = " ".join(sentences[:2])[:600]
            paper["summary_kind"] = "abstract_excerpt"
        venue_text = paper.get("venue", "")
        paper["priority_venues"] = [v["id"] for v in config["venues"] if re.search(v["regex"], venue_text, re.I)]
    return paper["classification"]["relevant"]


def validate(papers, config, edges=()):
    if contains_han(config):
        raise ValueError("Configuration prose must be in English")
    ids = set()
    for p in papers:
        if contains_han(p):
            raise ValueError(f"English metadata required: {p.get('id')}")
        if p.get("category") and p["category"] not in {"surveys", "routing", "other"}:
            raise ValueError(f"Invalid primary category: {p.get('id')}")
        for field in ("id", "title", "authors", "year", "url", "identifiers", "sources", "status", "tasks", "methods"):
            if field not in p:
                raise ValueError(f"Missing {field}: {p.get('id')}")
        if p["id"] in ids:
            raise ValueError(f"Duplicate id: {p['id']}")
        ids.add(p["id"])
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", p["id"]):
            raise ValueError(f"Invalid id: {p['id']}")
        if not isinstance(p["title"], str) or not p["title"].strip():
            raise ValueError(f"Empty title: {p['id']}")
        if p["status"] not in {"approved", "candidate", "rejected"}:
            raise ValueError(f"Invalid status: {p['id']}")
        if p["year"] is not None and (type(p["year"]) is not int or not 1800 <= p["year"] <= date.today().year + 1):
            raise ValueError(f"Invalid year: {p['id']}")
        if not p["url"].startswith("https://"):
            raise ValueError(f"HTTPS URL required: {p['id']}")
        if not set(p["tasks"]) <= config["tasks"].keys() or not set(p["methods"]) <= config["methods"].keys():
            raise ValueError(f"Unknown taxonomy label: {p['id']}")
        if not isinstance(p["authors"], list) or not all(isinstance(n, str) for n in p["authors"]):
            raise ValueError(f"Invalid authors: {p['id']}")
        for kind, values in p["identifiers"].items():
            if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
                raise ValueError(f"Invalid identifiers: {p['id']}/{kind}")
            if kind == "doi" and any(doi(v) != v for v in values):
                raise ValueError(f"DOI must be canonical: {p['id']}")
            if kind == "arxiv" and any(arxiv_id(v) != v for v in values):
                raise ValueError(f"arXiv id must be versionless: {p['id']}")
        if p["status"] == "approved" and (not p["tasks"] or not p.get("summary")):
            raise ValueError(f"Approved paper needs tasks and summary: {p['id']}")
        if p.get("venue_verified") and not p.get("venue_evidence"):
            raise ValueError(f"Verified venue needs evidence URL: {p['id']}")
    for i, a in enumerate(papers):
        for b in papers[i + 1:]:
            if same_paper(a, b):
                raise ValueError(f"Duplicate papers: {a['id']} / {b['id']}")
    for e in edges:
        if e["citing"] not in ids or e["cited"] not in ids or e["citing"] == e["cited"]:
            raise ValueError(f"Invalid citation edge: {e}")
