import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from pcb_lit.__main__ import main
from pcb_lit.core import arxiv_id, classify, doi, read_json, record, same_paper, upsert, validate, write_json
from pcb_lit.http import Client, FetchError
from pcb_lit.render import bibliography, md, render
from pcb_lit.sources import arxiv_search, crossref_search, parse_arxiv, parse_crossref, parse_s2, s2_neighbors

ROOT = Path(__file__).resolve().parent.parent
CONFIG = read_json(ROOT / "config.json")


def paper(title="PCB routing with constraints", **kwargs):
    return record(title, ["Alice Chen"], 2026, "https://example.org/paper", "fixture", **kwargs)


def atom(entries, total=None):
    body = '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/" xmlns:x="http://arxiv.org/schemas/atom">'
    body += f'<o:totalResults>{total if total is not None else len(entries)}</o:totalResults>'
    for aid, updated in entries:
        body += f'<entry><id>http://arxiv.org/abs/{aid}</id><title>PCB routing</title><author><name>Alice Chen</name></author><published>2025-12-01T00:00:00Z</published><updated>{updated}T00:00:00Z</updated><summary>Printed circuit board routing. A tool is proposed.</summary><x:doi>https://doi.org/10.1234/ABC</x:doi></entry>'
    return (body + '</feed>').encode()


class QueueClient:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.urls = []

    def get(self, url, headers=None):
        self.urls.append(url)
        return next(self.responses)

    json = get


class IdentityTests(unittest.TestCase):
    def test_identifier_normalization(self):
        self.assertEqual(doi("https://doi.org/10.1234/AbC"), "10.1234/abc")
        self.assertEqual(arxiv_id("https://arxiv.org/pdf/2601.12345v3.pdf"), "2601.12345")
        self.assertEqual(arxiv_id("https://arxiv.org/abs/cs/9901001v2"), "cs/9901001")

    def test_renamed_arxiv_version_merges(self):
        a = paper(identifiers={"arxiv": ["2602.00510"]})
        b = paper("New reward-guided title", identifiers={"arxiv": ["2602.00510"], "doi": ["10.1234/a"]})
        a.update(arxiv_updated="2026-01-01", arxiv_version="2602.00510v1")
        b.update(arxiv_updated="2026-06-17", arxiv_version="2602.00510v2")
        papers = [a]
        merged, added = upsert(papers, b)
        self.assertFalse(added)
        self.assertEqual(merged["title"], "New reward-guided title")
        self.assertEqual(merged["identifiers"]["doi"], ["10.1234/a"])

    def test_similar_title_is_not_enough(self):
        self.assertFalse(same_paper(paper("PCB routing: Part I"), paper("PCB routing: Part II")))
        a, b = paper(), paper()
        b["authors"] = ["Bob Li"]
        self.assertFalse(same_paper(a, b))

    def test_publication_and_preprint_exact_title_join(self):
        a = paper(identifiers={"arxiv": ["2601.12345"]})
        b = paper(identifiers={"doi": ["10.1234/a"]})
        self.assertTrue(same_paper(a, b))
        merged, _ = upsert([a], b)
        self.assertEqual(set(merged["identifiers"]), {"arxiv", "doi"})

    def test_editorial_decisions_survive_recrawl(self):
        a = paper(identifiers={"doi": ["10.1234/a"]})
        a.update(status="approved", summary="Checked note", tasks=["routing"], venue="DATE 2026")
        b = paper("Changed API title", identifiers={"doi": ["10.1234/a"]}, abstract="A very long abstract.")
        merged, _ = upsert([a], b)
        self.assertEqual(merged["title"], "PCB routing with constraints")
        self.assertEqual(merged["summary"], "Checked note")
        self.assertIn("fixture", merged["metadata_suggestions"])
        a["status"] = "rejected"
        upsert([a], b)
        self.assertEqual(a["status"], "rejected")

    def test_identifier_bridge_requires_manual_resolution(self):
        a = paper("One", identifiers={"doi": ["10.1234/a"]})
        b = paper("Two", identifiers={"arxiv": ["2601.12345"]})
        incoming = paper("Bridge", identifiers={"doi": ["10.1234/a"], "arxiv": ["2601.12345"]})
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            upsert([a, b], incoming)


class RelevanceTests(unittest.TestCase):
    def test_routing_accepted_inspection_and_chip_only_filtered(self):
        self.assertTrue(classify(paper(), CONFIG))
        self.assertTrue(classify(paper("OmniRouting: PCB routing benchmark"), CONFIG))
        self.assertFalse(classify(paper("PCB defect detection using neural networks"), CONFIG))
        self.assertFalse(classify(paper("A fast VLSI chip detailed router"), CONFIG))
        self.assertFalse(classify(paper("Polychlorinated biphenyl routing"), CONFIG))

    def test_label_and_excerpt_provenance(self):
        p = paper(abstract="A PCB routing benchmark is introduced. It uses reinforcement learning. Extra text.")
        classify(p, CONFIG)
        self.assertIn("benchmark", p["tasks"])
        self.assertIn("rl", p["methods"])
        self.assertEqual(p["summary_kind"], "abstract_excerpt")
        self.assertNotIn("Extra text", p["summary"])


class SourceTests(unittest.TestCase):
    def test_arxiv_version_year_and_doi(self):
        papers, total = parse_arxiv(atom([("2601.12345v2", "2026-11-09")]))
        self.assertEqual(total, 1)
        self.assertEqual(papers[0]["year"], 2025)
        self.assertEqual(papers[0]["identifiers"], {"arxiv": ["2601.12345"], "doi": ["10.1234/abc"]})

    def test_arxiv_updated_old_submission_is_included_and_stops(self):
        c = QueueClient(atom([("2601.12345v2", "2026-11-09"), ("2510.00001v1", "2026-09-01")], 100))
        records = list(arxiv_search(c, "PCB", "2026-11-01", page_size=2))
        self.assertEqual(len(records), 1)
        self.assertEqual(len(c.urls), 1)

    def test_page_cap_is_not_reported_as_complete(self):
        c = QueueClient(atom([("2601.12345v2", "2026-11-09")], 10))
        stream = arxiv_search(c, "PCB", "2026-11-01", max_pages=1, page_size=1)
        self.assertTrue(next(stream))
        with self.assertRaisesRegex(FetchError, "page cap"):
            next(stream)

    def test_arxiv_error_feed(self):
        feed = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#bad</id><summary>Bad query</summary></entry></feed>'
        with self.assertRaisesRegex(FetchError, "Bad query"):
            parse_arxiv(feed)

    def test_crossref_missing_date_and_abstract(self):
        p = parse_crossref({"DOI": "10.1234/ABC", "title": ["PCB Routing"], "published": {"date-parts": []}})
        self.assertIsNone(p["year"])
        self.assertEqual(p["abstract"], "")
        self.assertFalse(p["venue_verified"])

    def test_crossref_cursor_and_index_date(self):
        item = {"DOI": "10.1234/ABC", "title": ["PCB Routing"]}
        c = QueueClient({"message": {"items": [item], "next-cursor": "opaque+=x", "total-results": 2}},
                        {"message": {"items": [], "total-results": 2}})
        self.assertEqual(len(list(crossref_search(c, "PCB", "2026-01-01", page_size=1))), 1)
        qs = parse_qs(urlsplit(c.urls[1]).query)
        self.assertEqual(qs["cursor"], ["opaque+=x"])
        self.assertEqual(qs["filter"], ["from-index-date:2026-01-01"])

    def test_s2_null_records_and_graph_pagination(self):
        p = paper(identifiers={"arxiv": ["2601.12345"]})
        neighbor = {"paperId": "abc123", "title": "PCB fanout routing", "authors": [], "year": None, "abstract": None}
        c = QueueClient({"data": [{"citedPaper": None}], "next": 100}, {"data": [{"citedPaper": neighbor}]})
        result = list(s2_neighbors(c, p, "references"))
        self.assertEqual(result[0]["abstract"], "")
        self.assertIn("offset=100", c.urls[1])
        self.assertIsNone(parse_s2(None))


class HttpTests(unittest.TestCase):
    def test_http_failure_redacts_secret_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = Client(Path(tmp))
            error = HTTPError("https://example.org/?api_key=SECRET", 403, "forbidden", {}, None)
            with patch("pcb_lit.http.urlopen", side_effect=error), patch("pcb_lit.http.time.sleep"):
                with self.assertRaises(FetchError) as caught:
                    client.get("https://example.org/?api_key=SECRET")
            self.assertNotIn("SECRET", str(caught.exception))
            self.assertIn("403", str(caught.exception))

    def test_retry_after_long_delay_does_not_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            error = HTTPError("https://example.org", 429, "limit", {"Retry-After": "300"}, None)
            with patch("pcb_lit.http.urlopen", side_effect=error), patch("pcb_lit.http.time.sleep"):
                with self.assertRaisesRegex(FetchError, "later run"):
                    Client(Path(tmp)).get("https://example.org")


class WorkflowTests(unittest.TestCase):
    def setup_repo(self, tmp):
        root = Path(tmp)
        write_json(root / "config.json", CONFIG)
        write_json(root / "data/papers.json", [])
        write_json(root / "data/relations.json", [])
        (root / "README.md").write_text("# Test\n<!-- catalog:start --><!-- catalog:end -->\n", encoding="utf-8")
        return root

    def test_collect_review_render_reject_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.setup_repo(tmp)
            p = paper(identifiers={"arxiv": ["2601.12345"]}, abstract="A PCB routing benchmark. It works in KiCad.")
            with patch("pcb_lit.__main__.arxiv_search", return_value=iter([p])):
                self.assertEqual(main(["--root", tmp, "collect", "--sources", "arxiv"]), 0)
            self.assertIn("1 candidates", (root / "INBOX.md").read_text(encoding="utf-8"))
            main(["--root", tmp, "review", p["id"], "approved", "--tasks", "routing", "--summary", "Verified note"])
            before = (root / "README.md").read_bytes()
            main(["--root", tmp, "render"])
            self.assertEqual(before, (root / "README.md").read_bytes())
            self.assertIn("@misc{", (root / "references.bib").read_text(encoding="utf-8"))
            main(["--root", tmp, "review", p["id"], "rejected"])
            self.assertNotIn(p["title"], (root / "README.md").read_text(encoding="utf-8"))

    def test_graph_direction_and_non_pcb_neighbors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.setup_repo(tmp)
            seed = paper("PCB route seed", identifiers={"arxiv": ["2601.12345"]})
            seed.update(status="approved", tasks=["routing"], summary="A checked note")
            write_json(root / "data/papers.json", [seed])
            older, newer = paper("PCB routing older"), paper("PCB routing newer")
            unrelated = paper("Verilog code generation")
            with patch("pcb_lit.__main__.arxiv_search", return_value=iter([])), patch("pcb_lit.__main__.arxiv_refresh", return_value=iter([])), patch("pcb_lit.__main__.s2_neighbors", side_effect=[iter([older, unrelated]), iter([newer])]):
                self.assertEqual(main(["--root", tmp, "collect", "--sources", "arxiv", "--graph"]), 0)
            edges = read_json(root / "data/relations.json")
            self.assertIn({"citing": seed["id"], "cited": older["id"], "source": "semantic_scholar"}, edges)
            self.assertIn({"citing": newer["id"], "cited": seed["id"], "source": "semantic_scholar"}, edges)
            self.assertEqual(len(read_json(root / "data/papers.json")), 3)

    def test_all_sources_failure_is_nonzero_even_with_allow_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.setup_repo(tmp)
            with patch("pcb_lit.__main__.arxiv_search", side_effect=lambda *a, **k: failing_stream()):
                self.assertEqual(main(["--root", tmp, "collect", "--sources", "arxiv", "--allow-partial"]), 2)
            self.assertTrue(read_json(root / ".reports/latest.json")["warnings"])

    def test_unsafe_markdown_is_escaped_and_bibtex_has_authors(self):
        self.assertIn(r"\|", md("x|y"))
        p = paper("PCB routing {special} & test")
        p.update(status="approved", tasks=["routing"], summary="Checked")
        bib = bibliography([p])
        self.assertIn(r"\{special\}", bib)
        self.assertIn("Alice Chen", bib)
        self.assertNotIn("booktitle", bib)

    def test_repository_catalog_valid(self):
        validate(read_json(ROOT / "data/papers.json"), CONFIG, read_json(ROOT / "data/relations.json"))


def failing_stream():
    raise FetchError("arxiv: HTTP 503")
    yield  # make failure occur while iterating, just like a provider


if __name__ == "__main__":
    unittest.main()
