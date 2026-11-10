# Maintenance

## Local development

Use Python 3.11 or later. The collector uses only the Python standard library.

```bash
git clone https://github.com/tikyttqq/Awesome-PCB-Routing.git
cd Awesome-PCB-Routing
python -m unittest discover -s tests -v
python -m pcb_lit validate
python -m pcb_lit render
```

The README is the public literature collection. Collection commands, review operations, and automation settings are documented here. Additional browsing views are generated in [by-year.md](by-year.md), [by-method.md](by-method.md), [by-task.md](by-task.md), and [by-venue.md](by-venue.md).

## Literature discovery

```bash
# Search a rolling 28-day window.
python -m pcb_lit collect

# Query one source or request a historical backfill.
python -m pcb_lit collect --sources arxiv --days 28
python -m pcb_lit collect --sources crossref --since 2026-01-01 --max-pages 10

# Expand one seed's references and citing papers.
python -m pcb_lit collect --sources arxiv --graph --seed pcbrouteagent2026
```

Configure search expressions, relevance rules, public sections, task tags, methods, and venue priorities in `config.json`. arXiv results are ordered by update time; Crossref uses the indexing date to catch newly indexed and revised metadata. Page caps produce explicit warnings. Split broad queries or increase the cap when backfilling; capped results do not establish complete coverage.

The optional environment variables are:

| Variable | Purpose |
| --- | --- |
| `CONTACT_EMAIL` | Contact address for API identification and Crossref's polite pool |
| `S2_API_KEY` | Semantic Scholar authentication for citation expansion |

Set credentials in the environment or GitHub Actions secrets. Do not place them in catalog records or configuration files. Cache and diagnostic files are excluded from version control.

## Review and publication

New discoveries are saved as candidates in `data/papers.json` and listed in `INBOX.md`. Check the primary source, PCB relevance, title, authors, year, task labels, and available code or project pages before approval.

```bash
python -m pcb_lit review PAPER_ID approved --category routing --summary "An original, source-checked description of the contribution."
python -m pcb_lit review PAPER_ID rejected
python -m pcb_lit validate
python -m pcb_lit render
```

Each paper has one primary category: `surveys`, `routing`, or `other`. Survey articles are listed under Surveys; routing algorithms and routing-focused benchmarks under PCB Routing; schematic generation, placement, and layout migration under Other PCB Design. Task and method tags can overlap internally, but public category listings contain each paper exactly once.

For browser-only review after this workflow is merged into the default branch:

1. Open the bot update PR and read `INBOX.md` under **Files changed**. Check the paper source and copy its record ID.
2. Open **Actions > Review paper > Run workflow** on the default branch. Supply the ID, decision, category, and an original English contribution note when approving.
3. Wait for the workflow to update the bot PR. Check the regenerated README and merge that PR when the reviewed batch is ready.

The review workflow expects the `automation/update-papers` branch created by **Update literature**. Run discovery first if no update branch exists. Clicking GitHub's general **Approve** button alone does not change a candidate's catalog status. Review whenever a meaningful update PR arrives; a weekly review is usually sufficient for a small collection. Review decisions should be merged before the next scheduled discovery run, which recalculates the bot branch from the default branch. No review is needed at the scheduled midnight execution time itself.

Rejected identities are retained to prevent repeated discovery. Approved metadata and reading notes are preserved during collection; API disagreements appear in `metadata_suggestions`. Merge duplicate identities conservatively, union their identifiers and sources, and update citation endpoints.

Keep repository prose and filenames in English. The collector skips metadata containing CJK ideographs and reports the number in `filtered_non_english`; a maintainer can add a verified English record separately. Validation also checks catalog records and configuration. Candidate summaries are explicitly marked abstract excerpts; approved notes should be original descriptions based on the paper.

Set `venue_verified` only when a primary source supports the publication claim, and provide `venue_evidence`. Conference proceedings, workshops, journals, and preprints remain distinct publication types. The public tables display compact venue information; evidence and verification metadata remain available in the machine-readable catalog.

Store implementation and project links under `links.code` and `links.project`. These are the only link types displayed in the `Code` column. The paper title links to the paper itself; missing implementation links leave an empty cell.

## Scheduled updates

The **Update literature** workflow is scheduled for **00:00 UTC every day**, using `0 0 * * *`. GitHub may delay scheduled jobs. Monday runs also expand one-hop references and citations. Scheduled workflows run from the default branch, so workflow changes take effect after merging.

1. In **Settings > Actions > General > Workflow permissions**, allow GitHub Actions to create pull requests. Organization policies must also permit this.
2. Optionally set the repository variable `CONTACT_EMAIL` and the Actions secret `S2_API_KEY`.
3. Run **Update literature** manually to check setup. Set `graph` to expand citations or supply `since` for a historical backfill.
4. Review the `crawl-report` artifact and the `automation/update-papers` pull request. Review candidate records on that branch, regenerate the catalog, and merge the changes.

The workflow searches the preceding 28 days on each run, updates the same bot branch, and runs offline tests and metadata validation before creating a PR. Source failures and pagination limits appear in the report and PR description. Partial collection may produce a PR; it is not treated as complete source coverage. All-source failures still fail the run.

New candidates persist on the default branch only after merging the update PR. After an interruption longer than the search window, run a manual backfill. The default `GITHUB_TOKEN` does not normally trigger other workflows when it creates a PR, so the update workflow performs its own validation.

## Repository structure

```text
config.json                 Search rules, taxonomy, and venue priorities
data/papers.json            Canonical paper records and review status
data/relations.json         Citation edges and provenance
pcb_lit/                    API clients, identity handling, rendering, and CLI
scripts/                    Source checks and seed bootstrap utility
tests/                      Offline behavior and presentation checks
docs/                       Maintenance, methodology, and browsing views
.github/workflows/          Validation and scheduled update workflows
INBOX.md                    Candidate review queue
references.bib              Generated bibliography
papers.csv                  Generated catalog export
```

Use `python scripts/check_sources.py` to check known papers against the live APIs. The command saves a diagnostic report in `.reports/source-smoke.json` without modifying the catalog. See [TESTING.md](TESTING.md) for validation guidance and [METHODOLOGY.md](METHODOLOGY.md) for collection scope and source limitations.
