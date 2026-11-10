# Contributing

Contributions of relevant papers, benchmarks, datasets, code, and corrections are welcome. Open a paper suggestion issue with a primary source URL, or submit a pull request against `main`.

## Suggesting a paper

Include the exact title, authors, publication year, DOI or arXiv ID where available, the PCB design task, and a short description of the contribution. Add official implementation and project links when available. Distinguish main-conference papers, workshop papers, journal articles, and preprints; venue claims should have a primary source.

The collection covers PCB routing and adjacent board-level design tasks. Inspection-only papers, chemistry papers using the PCB acronym, generic chip-only EDA, packet routing, and surface-mount machine motion planning are outside its primary scope. See [the methodology](docs/METHODOLOGY.md) for the inclusion policy.

## Editing the catalog

Edit `data/papers.json`, then validate and regenerate the views:

```bash
python -m unittest discover -s tests -v
python -m pcb_lit validate
python -m pcb_lit render
```

Keep prose, notes, and filenames in English. Use `links.code` for an implementation and `links.project` for its project page. The public tables show these links in the `Code` column; source evidence remains in the catalog metadata.

New automatic discoveries remain candidates until reviewed. Use `python -m pcb_lit review ID approved --category routing --summary "A source-checked contribution note"` to approve one. The **Review paper** workflow also applies decisions to the literature update PR through GitHub Actions. Keep rejected identities to avoid repeated discovery. Do not edit generated paper tables directly.

To record a confirmed publication, update `venue`, `publication_type`, `venue_verified`, and `venue_evidence`. Each record has exactly one primary `category`: `surveys`, `routing`, or `other`. Surveys take precedence; routing algorithms, escape/fanout, and routing benchmarks belong to `routing`; schematic generation, placement, and design migration belong to `other`. For mixed-task papers, choose the main contribution. The README lists each paper once and sorts each section by year. Task and method tags describe the paper without duplicating its public entry.

When consolidating duplicates, preserve the chosen record's ID, combine identifiers and sources, update citation endpoints, and remove duplicate or self-referencing edges. Preserve editorial notes and review decisions deliberately.

See [maintenance documentation](docs/MAINTENANCE.md) for collection commands, API configuration, and the daily update workflow.
