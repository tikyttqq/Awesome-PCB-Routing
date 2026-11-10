from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import quote, urlencode

from .core import arxiv_id, clean, doi, record
from .http import FetchError

NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}


def parse_arxiv(body):
    try:
        root = ET.fromstring(body)
        total = int(root.findtext("o:totalResults", "0", NS))
        papers = []
        for e in root.findall("a:entry", NS):
            raw_id = e.findtext("a:id", "", NS)
            if "api/errors" in raw_id:
                raise FetchError("arxiv: " + clean(e.findtext("a:summary", "API error", NS)))
            aid = arxiv_id(raw_id)
            published = e.findtext("a:published", "", NS)
            if not aid or not published:
                raise FetchError("arxiv: missing id/publication date")
            identifiers = {"arxiv": [aid]}
            raw_doi = e.findtext("x:doi", "", NS)
            if raw_doi:
                identifiers["doi"] = [doi(raw_doi)]
            p = record(e.findtext("a:title", "", NS),
                       [clean(a.findtext("a:name", "", NS)) for a in e.findall("a:author", NS)],
                       int(published[:4]), "https://arxiv.org/abs/" + aid, "arxiv",
                       abstract=e.findtext("a:summary", "", NS), identifiers=identifiers)
            p.update(publication_type="preprint", arxiv_updated=e.findtext("a:updated", published, NS),
                     arxiv_version=raw_id.rsplit("/", 1)[-1], journal_ref=clean(e.findtext("x:journal_ref", "", NS)))
            papers.append(p)
        return papers, total
    except (ET.ParseError, ValueError) as exc:
        raise FetchError(f"arxiv: malformed Atom feed ({type(exc).__name__})") from None


def arxiv_search(client, query, since, max_pages=5, page_size=100):
    for page in range(max_pages):
        params = dict(search_query=query, start=page * page_size, max_results=page_size,
                      sortBy="lastUpdatedDate", sortOrder="descending")
        papers, total = parse_arxiv(client.get("https://export.arxiv.org/api/query?" + urlencode(params)))
        for p in papers:
            if p["arxiv_updated"][:10] >= since:
                yield p
        if not papers or len(papers) < page_size or (page + 1) * page_size >= total:
            return
        if papers[-1]["arxiv_updated"][:10] < since:
            return
    raise FetchError("arxiv: page cap reached; split query/increase --max-pages (coverage incomplete)")


def arxiv_refresh(client, ids):
    for start in range(0, len(ids), 100):
        params = urlencode({"id_list": ",".join(ids[start:start + 100]), "max_results": 100})
        papers, _ = parse_arxiv(client.get("https://export.arxiv.org/api/query?" + params))
        yield from papers


def parse_crossref(item):
    title = clean(" ".join(item.get("title", [])))
    if not title or not item.get("DOI"):
        return None
    parts = []
    for field in ("published", "published-print", "published-online", "issued"):
        dates = (item.get(field) or {}).get("date-parts") or [[]]
        parts = dates[0]
        if parts:
            break
    did = doi(item["DOI"])
    authors = [clean(a.get("name") or (a.get("given", "") + " " + a.get("family", ""))) for a in item.get("author", [])]
    p = record(title, authors, parts[0] if parts else None, "https://doi.org/" + did,
               "crossref", abstract=item.get("abstract", ""), identifiers={"doi": [did]})
    p.update(venue=clean("; ".join(item.get("container-title", []))),
             publication_type={"journal-article": "journal", "proceedings-article": "conference", "posted-content": "preprint"}.get(item.get("type"), "unknown"))
    return p


def crossref_search(client, query, since, contact="", max_pages=5, page_size=100):
    cursor = "*"
    for page in range(max_pages):
        params = {"query.bibliographic": query, "filter": "from-index-date:" + since,
                  "rows": page_size, "cursor": cursor}
        if contact:
            params["mailto"] = contact
        message = client.json("https://api.crossref.org/works?" + urlencode(params))["message"]
        items = message.get("items", [])
        for item in items:
            p = parse_crossref(item)
            if p:
                yield p
        if len(items) < page_size or (page + 1) * page_size >= message.get("total-results", 0):
            return
        nxt = message.get("next-cursor")
        if not nxt or nxt == cursor:
            raise FetchError("crossref: cursor did not advance (coverage incomplete)")
        cursor = nxt
    raise FetchError("crossref: page cap reached; split query/increase --max-pages (coverage incomplete)")


S2_FIELDS = "paperId,title,authors,year,abstract,venue,url,externalIds,publicationTypes"


def s2_locator(p):
    ids = p["identifiers"]
    for key, prefix in (("semantic_scholar", ""), ("doi", "DOI:"), ("arxiv", "ARXIV:")):
        if ids.get(key):
            return prefix + ids[key][0]
    return None


def parse_s2(item):
    if not item or not item.get("title") or not item.get("paperId"):
        return None
    ids = {"semantic_scholar": [item["paperId"]]}
    ext = item.get("externalIds") or {}
    if ext.get("DOI"):
        ids["doi"] = [doi(ext["DOI"])]
    if ext.get("ArXiv"):
        ids["arxiv"] = [arxiv_id(ext["ArXiv"])]
    url = "https://www.semanticscholar.org/paper/" + item["paperId"]
    p = record(item["title"], [a["name"] for a in item.get("authors", [])], item.get("year"),
               url, "semantic_scholar", abstract=item.get("abstract") or "", identifiers=ids)
    p["venue"] = item.get("venue") or ""
    kinds = item.get("publicationTypes") or []
    p["publication_type"] = "journal" if "JournalArticle" in kinds else "conference" if "Conference" in kinds else "unknown"
    return p


def s2_neighbors(client, paper, direction, api_key="", max_pages=5, page_size=100):
    locator = s2_locator(paper)
    if not locator:
        return
    headers = {"x-api-key": api_key} if api_key else {}
    base = "https://api.semanticscholar.org/graph/v1/paper/" + quote(locator, safe="")
    offset = 0
    for _ in range(max_pages):
        message = client.json(base + "/" + direction + "?" + urlencode({"fields": S2_FIELDS, "limit": page_size, "offset": offset}), headers)
        if "data" not in message:
            raise FetchError("semantic_scholar: missing data")
        key = "citedPaper" if direction == "references" else "citingPaper"
        for item in message["data"]:
            p = parse_s2(item.get(key))
            if p:
                yield p
        nxt = message.get("next")
        if nxt is None:
            return
        if nxt <= offset:
            raise FetchError("semantic_scholar: offset did not advance")
        offset = nxt
    raise FetchError("semantic_scholar: page cap reached (coverage incomplete)")
