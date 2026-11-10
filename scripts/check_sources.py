"""Small live API smoke check; saves diagnostics without changing the catalog."""
from pathlib import Path
import argparse
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pcb_lit.core import write_json
from pcb_lit.http import Client, FetchError
from pcb_lit.sources import arxiv_refresh, parse_crossref, parse_s2

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", nargs="+", choices=["arxiv", "crossref", "s2"], default=["arxiv", "crossref", "s2"])
    args = parser.parse_args()
    client = Client(ROOT / ".cache/http", os.getenv("CONTACT_EMAIL", ""))
    report = {}
    for provider in args.providers:
        try:
            if provider == "arxiv":
                p = next(arxiv_refresh(client, ["2210.14259"]))
            elif provider == "crossref":
                p = parse_crossref(client.json("https://api.crossref.org/works/10.1145%2F3394885.3431568")["message"])
            else:
                key = os.getenv("S2_API_KEY", "")
                headers = {"x-api-key": key} if key else {}
                p = parse_s2(client.json("https://api.semanticscholar.org/graph/v1/paper/ARXIV:2210.14259?fields=paperId,title,authors,year,abstract,venue,url,externalIds,publicationTypes", headers))
            if not p or "printed circuit board" not in p["title"].lower():
                raise FetchError("Response did not match expected PCB paper")
            report[provider] = {"ok": True, "title": p["title"], "identifiers": p["identifiers"]}
        except (FetchError, StopIteration, KeyError, ValueError) as exc:
            report[provider] = {"ok": False, "error": str(exc) if isinstance(exc, FetchError) else type(exc).__name__}
        print(provider + ": " + ("OK" if report[provider]["ok"] else report[provider]["error"]), flush=True)
    write_json(ROOT / ".reports/source-smoke.json", report)
    return 0 if all(v["ok"] for v in report.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
