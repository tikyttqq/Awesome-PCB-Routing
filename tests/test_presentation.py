import copy
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pcb_lit.__main__ import main
from pcb_lit.core import catalog_category, contains_han, read_json, record, validate, write_json
from pcb_lit.render import render, table

ROOT = Path(__file__).resolve().parent.parent
CONFIG = read_json(ROOT / "config.json")
PAPERS = read_json(ROOT / "data/papers.json")


class PublicPresentationTests(unittest.TestCase):
    def test_tables_keep_only_paper_code_and_project_links(self):
        p = copy.deepcopy(PAPERS[0])
        p["links"] = {"code": "https://example.org/code", "project": "https://example.org/project",
                      "dataset": "https://example.org/data"}
        p["venue_evidence"] = "https://example.org/evidence"
        output = table([p], CONFIG)
        self.assertIn("| Paper | Year | Venue | Code |", output)
        self.assertIn("[Code](https://example.org/code)", output)
        self.assertIn("[Project](https://example.org/project)", output)
        self.assertNotIn("https://example.org/data", output)
        self.assertNotIn("https://example.org/evidence", output)
        self.assertNotIn("[source]", output)

    def test_missing_code_leaves_empty_cell_and_project_can_stand_alone(self):
        p = copy.deepcopy(PAPERS[0])
        p["links"] = {}
        self.assertTrue(table([p], CONFIG).splitlines()[-1].endswith(" |  |"))
        p["links"] = {"project": "https://example.org/project"}
        self.assertIn("[Project](https://example.org/project)", table([p], CONFIG))

    def test_render_preserves_public_readme_and_sorts_each_topic(self):
        papers = [copy.deepcopy(p) for p in PAPERS]
        candidate = copy.deepcopy(papers[0])
        candidate.update(id="candidate-only", title="Candidate only paper", status="candidate")
        papers.append(candidate)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text((ROOT / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
            render(root, papers, CONFIG)
            first = (root / "README.md").read_bytes()
            render(root, papers, CONFIG)
            self.assertEqual(first, (root / "README.md").read_bytes())
            text = (root / "README.md").read_text(encoding="utf-8")
            for spec in CONFIG["sections"].values():
                self.assertIn("## " + spec["label"], text)
            self.assertNotIn("Candidate only paper", text)
            self.assertNotIn("Quick Start", text)
            self.assertNotIn("mermaid", text)
            self.assertNotIn("## Reviewed", text)
            self.assertNotIn("python -m", text)
            section = text.split("## PCB Routing\n", 1)[1].split("\n## ", 1)[0]
            self.assertLess(section.index("PCBRouteAgent"), section.index("GPCB Routing"))
            self.assertFalse(contains_han(text))
            from pcb_lit.render import link
            for p in PAPERS:
                if p["status"] != "approved":
                    continue
                for filename in ("README.md", "docs/by-task.md", "docs/by-method.md"):
                    content = (root / filename).read_text(encoding="utf-8")
                    self.assertEqual(content.count(link(p["title"], p["url"])), 1, p["id"] + ": " + filename)

    def test_primary_categories_do_not_follow_every_task_tag(self):
        p = record("PCB schematic generation", [], 2026, "https://example.org/schematic", "test")
        p["tasks"] = ["schematic", "routing", "benchmark", "constraints"]
        self.assertEqual(catalog_category(p), "other")
        p["title"] = "A survey of PCB routing"
        self.assertEqual(catalog_category(p), "surveys")
        p.update(title="PCBWorld", tasks=["routing", "benchmark"])
        self.assertEqual(catalog_category(p), "routing")
        p.update(title="PCB-Migrator: Automated PCB PnR Migration", category="other")
        self.assertEqual(catalog_category(p), "other")

    def test_review_sets_one_primary_category_and_publishes_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = record("Mixed PCB placement and routing", [], 2026, "https://example.org/mixed", "test")
            p["tasks"] = ["placement", "routing", "benchmark"]
            write_json(root / "config.json", CONFIG)
            write_json(root / "data/papers.json", [p])
            write_json(root / "data/relations.json", [])
            (root / "README.md").write_text("<!-- catalog:start --><!-- catalog:end -->", encoding="utf-8")
            with redirect_stdout(StringIO()):
                main(["--root", tmp, "review", p["id"], "approved", "--category", "other", "--summary", "A verified mixed-task contribution."])
            stored = read_json(root / "data/papers.json")[0]
            self.assertEqual(stored["category"], "other")
            output = (root / "README.md").read_text(encoding="utf-8")
            self.assertEqual(output.count(p["title"]), 1)
            self.assertIn(p["title"], output.split("## Other PCB Design", 1)[1])

    def test_english_catalog_policy_is_enforced_during_validation(self):
        papers = copy.deepcopy(PAPERS)
        papers[0]["summary"] = "\u8def\u7531"
        with self.assertRaisesRegex(ValueError, "English metadata required"):
            validate(papers, CONFIG)

    def test_collection_skips_non_english_imports_without_losing_english_records(self):
        english = record("PCB routing benchmark", ["Alice Chen"], 2026, "https://example.org/paper", "test")
        other = record("PCB routing \u8def\u7531", ["Alice Chen"], 2026, "https://example.org/other", "test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "config.json", CONFIG)
            write_json(root / "data/papers.json", [])
            write_json(root / "data/relations.json", [])
            with patch("pcb_lit.__main__.arxiv_search", return_value=iter([other, english])), redirect_stdout(StringIO()):
                result = main(["--root", tmp, "collect", "--sources", "arxiv"])
            self.assertEqual(result, 0)
            stored = read_json(root / "data/papers.json")
            self.assertEqual([p["title"] for p in stored], [english["title"]])
            self.assertEqual(read_json(root / ".reports/latest.json")["filtered_non_english"], 1)

    def test_repository_text_and_filenames_are_english(self):
        ignored = {".git", ".cache", ".reports", "__pycache__", ".venv"}
        suffixes = {".md", ".py", ".json", ".csv", ".bib", ".yml", ".yaml"}
        for path in ROOT.rglob("*"):
            relative = path.relative_to(ROOT)
            if set(relative.parts) & ignored:
                continue
            self.assertFalse(contains_han(str(relative)), str(relative))
            if path.is_file() and path.suffix in suffixes:
                self.assertFalse(contains_han(path.read_text(encoding="utf-8")), str(relative))
        self.assertTrue((ROOT / "docs/MAINTENANCE.md").exists())
        self.assertFalse(list((ROOT / "docs").glob("*.zh-*.md")))


if __name__ == "__main__":
    unittest.main()
