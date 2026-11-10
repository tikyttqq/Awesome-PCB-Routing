# Testing

Run the offline checks from the repository root with Python 3.11 or later:

```bash
python -m unittest discover -s tests -v
python -m pcb_lit validate
python -m pcb_lit render
git diff --exit-code -- README.md INBOX.md docs/by-year.md docs/by-task.md docs/by-method.md docs/by-venue.md docs/notes.md references.bib papers.csv
```

The tests cover identifier normalization, version merging, preservation of editorial decisions, relevance filtering, API pagination, partial failures, citation direction, catalog generation, and the public presentation contract, exclusive primary categories, and publication of reviewed records without duplicate listings. Generated views must be reproducible from the canonical JSON records. The presentation checks also verify that repository prose and filenames contain no CJK ideographs.

The CI workflow runs these offline checks for pushes and pull requests. After editing metadata, regenerate the derived files and commit them together so CI can verify that the catalog is current.

## Optional live checks

```bash
python scripts/check_sources.py
python scripts/check_sources.py --providers crossref
```

Live checks retrieve known papers and verify that their titles match the expected PCB subject. They save provider results to `.reports/source-smoke.json` without changing paper records. A timeout or HTTP 429 is a failed provider check, not evidence that no new literature exists. Configure `S2_API_KEY` when using authenticated Semantic Scholar access.

GitHub schedule execution and bot PR creation require enabled Actions permissions. Inspect the first workflow run and its report artifact after configuring or changing automation. The schedule is 00:00 UTC daily; actual job start times depend on GitHub's scheduler.
