from __future__ import annotations

import csv
import io
import re
from urllib.parse import quote

from .core import catalog_category, write_text


def md(value):
    value = str(value or "").replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*{}\[\]<>()|_])", r"\\\1", value)


def link(label, url):
    # Encode delimiters so untrusted titles/URLs cannot break Markdown tables.
    return f"[{md(label)}]({quote(url, safe=':/?=&%#@+~')})"


def venue(p):
    if p.get("venue"):
        return p["venue"]
    return "arXiv" if p.get("publication_type") == "preprint" else "—"


def table(papers, config):
    rows = ["| Paper | Year | Venue | Code |", "| --- | --- | --- | --- |"]
    for p in papers:
        resources = [link(label, p["links"][key]) for key, label in (("code", "Code"), ("project", "Project"))
                     if p.get("links", {}).get(key)]
        rows.append(f"| {link(p['title'], p['url'])} | {p['year'] or '—'} | {md(venue(p))} | {' · '.join(resources)} |")
    return "\n".join(rows) + "\n"


def topic_catalog(papers, config):
    sections = []
    for key, spec in config["sections"].items():
        sections.append(f"## {spec['label']}\n")
        if spec.get("description"):
            sections.append(spec["description"] + "\n")
        selected = [p for p in papers if catalog_category(p) == key]
        sections.append(table(selected, config) if selected else "Contributions are welcome.\n")
    return "\n".join(sections)


def bib_escape(value):
    mapping = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "$": r"\$"}
    return "".join(mapping.get(c, c) for c in str(value))


def bibliography(papers):
    blocks = []
    for p in papers:
        kind = {"journal": "article", "conference": "inproceedings", "workshop": "inproceedings"}.get(p.get("publication_type"), "misc") if p.get("venue_verified") else "misc"
        fields = {"title": "{" + bib_escape(p["title"]) + "}",
                  "author": " and ".join(bib_escape(a) for a in p["authors"]),
                  "url": p["url"]}
        if p["year"]:
            fields["year"] = str(p["year"])
        if kind != "misc":
            fields["journal" if kind == "article" else "booktitle"] = bib_escape(p["venue"])
        if p["identifiers"].get("doi"):
            fields["doi"] = p["identifiers"]["doi"][0]
        if p["identifiers"].get("arxiv"):
            fields.update(eprint=p["identifiers"]["arxiv"][0], archivePrefix="arXiv")
        blocks.append("@" + kind + "{" + p["id"] + ",\n" + "".join(f"  {k} = {{{v}}},\n" for k, v in fields.items()) + "}\n")
    return "\n".join(blocks)


def render(root, papers, config):
    approved = sorted((p for p in papers if p["status"] == "approved"), key=lambda p: (-(p["year"] or 0), p["title"].lower()))
    candidates = sorted((p for p in papers if p["status"] == "candidate"), key=lambda p: (-(p["year"] or 0), p["title"].lower()))
    year_lines = ["# Papers by year\n", "Year = canonical record year; arXiv uses first submission year. See sources for online/print differences.\n"]
    for year in sorted({p["year"] for p in approved}, key=lambda y: y or 0, reverse=True):
        year_lines += [f"## {year or 'Unknown'}\n", table([p for p in approved if p["year"] == year], config)]
    write_text(root / "docs/by-year.md", "\n".join(year_lines))
    write_text(root / "docs/by-task.md", "# Papers by Category\n\n" + topic_catalog(approved, config))
    method_lines = ["# Method Tags\n", "Methods describe the approach; each paper is listed once in the table below.\n",
                    "| Paper | Method tags |", "| --- | --- |"]
    for p in approved:
        labels = [config["methods"][key]["label"] for key in p["methods"]]
        method_lines.append(f"| {link(p['title'], p['url'])} | {md(', '.join(labels))} |")
    write_text(root / "docs/by-method.md", "\n".join(method_lines) + "\n")
    lines = ["# Papers by venue\n", "Publication details and source evidence are recorded in [the catalog](../data/papers.json).\n"]
    for name in sorted({venue(p) for p in approved}):
        lines += [f"## {md(name)}\n", table([p for p in approved if venue(p) == name], config)]
    write_text(root / "docs/by-venue.md", "\n".join(lines))
    lines = ["# Reading notes\n", "Human-written notes for approved records. Automatic excerpts are marked in the inbox.\n"]
    for p in approved:
        lines += [f"## {md(p['title'])}\n", f"`{p['id']}` · {link('Paper', p['url'])}\n", md(p.get("summary", "")) + "\n"]
    write_text(root / "docs/notes.md", "\n".join(lines))
    inbox = ["# Review inbox\n", f"{len(candidates)} candidates. Automatic tags and abstract excerpts need review before inclusion.\n", table(candidates, config)]
    for p in candidates:
        inbox += [f"## {md(p['title'])}\n", f"ID: `{p['id']}` · suggested venue priority: {md(', '.join(p.get('priority_venues', [])) or 'none')}\n",
                  md(p.get("summary") or "No abstract available; read the source before reviewing.") + "\n",
                  "Classification evidence: `" + str(p.get("classification", {})).replace("`", "") + "`\n"]
    write_text(root / "INBOX.md", "\n".join(inbox))
    write_text(root / "references.bib", bibliography(approved))
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["id", "year", "title", "venue", "category", "tasks", "methods", "url"])
    for p in approved:
        cells = [p["id"], p["year"], p["title"], venue(p), catalog_category(p), ";".join(p["tasks"]), ";".join(p["methods"]), p["url"]]
        # Prevent formula interpretation when opening third-party metadata in Excel.
        writer.writerow(["'" + str(v) if str(v or "").startswith(("=", "+", "-", "@", "\t")) else v for v in cells])
    write_text(root / "papers.csv", output.getvalue())
    readme = root / "README.md"
    if readme.exists():
        start, end = "<!-- catalog:start -->", "<!-- catalog:end -->"
        body = "\n\n" + topic_catalog(approved, config) + "\n"
        text = readme.read_text(encoding="utf-8")
        if text.count(start) != 1 or text.count(end) != 1:
            raise ValueError("README catalog markers missing/duplicated")
        before, tail = text.split(start)
        _, after = tail.split(end)
        write_text(readme, before + start + body + end + after)
