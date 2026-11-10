# Scope, provenance and coverage

## Inclusion policy

The primary domain is board-level routing: global/detail routing, multilayer routing, escape/fanout, differential pairs, length matching, routability, DRC and electrical/thermal constraints. Placement, schematic synthesis, layout migration and benchmark environments are adjacent tracks. Classical algorithms and learning-based methods are both eligible. Selected general routing foundations can be manually included with an explanation.

PCB defect inspection, manufacturing defect classification, polychlorinated biphenyl chemistry, and generic chip-only EDA are outside the automatic inclusion scope. An IC paper is not PCB research merely because a PCB paper cites it. A reference/citation edge is a discovery signal, not proof of relevance.

## Discovery channels

| Channel | Implemented purpose | Important limits |
| --- | --- | --- |
| arXiv Atom API | Search titles/abstracts; newest updates first; refresh approved arXiv IDs | Not every paper is on arXiv; query/index lag; capped pagination |
| Crossref REST | Discover journal/conference DOI metadata; indexed-since window | Fuzzy queries are noisy; incomplete abstracts/DOI deposits; page caps |
| Semantic Scholar Graph | One-hop references and citing papers, paginated independently | Coverage/indexing delays; null abstracts; public API rate limiting; very new preprints may be absent |
| Manual primary-source checks | Conference proceedings, author pages, paper bibliographies | Human effort; evidence and review date must be recorded |

References are older works cited by a seed (backward expansion); citations are works citing a seed (forward expansion). Both map to the stored edge direction **citing → cited**. Only PCB-relevant or already cataloged neighbors are retained; excluded neighbors are counted in the report. The graph is a selected discovery graph, not a complete bibliography graph. All approved nodes become eligible seeds on subsequent graph runs.

## Classification and summarization

The collector maintains English metadata and skips records containing CJK ideographs, counting them in the run report. The default classifier requires a PCB/board context and design-task signal, then applies a title exclusion rule. It records the boolean evidence, rule version and suggested labels. Task and method tags are multi-valued. Each paper has one primary public category (`surveys`, `routing`, or `other`), and each public category index lists it exactly once. Survey articles take precedence; mixed-task papers are assigned by their main contribution. Approved manual categories and labels are preserved. Rule-based filtering can both miss relevant papers and include false positives; review and negative examples are needed.

Automatic summaries are **extractive abstract excerpts**, limited to the first two sentences and 600 characters. They do not inspect full papers, generate benchmark results, infer datasets or claim replication. Approved records use human-written notes. An optional future LLM layer should suggest structured tags/notes with evidence spans, remain separate from verified metadata and never promote venue claims without checking a primary source. No paid model API is needed by this implementation.

## Venue evidence

The watchlist includes major EDA conferences/journals and related AI venues. It is a priority list, not an authoritative ranking or a source whitelist. Keywords are searched across indexed literature; venue matching highlights candidates but does not prove acceptance. Workshop, main conference, journal and preprint are separate publication types.

`venue_verified` requires `venue_evidence`. The initial PCBWorld venue is an explicitly named KDD workshop, PCB-Bench uses the ICLR proceedings, and ModuPlace uses the author's camera-ready PDF. Some foundational entries have venue information transcribed from paper bibliographies; their unverified status is retained in the underlying catalog metadata. Public tables show venue names, while sources and verification evidence remain in `data/papers.json`. PCBSchemaGen uses its current arXiv v2 title; an arXiv DOI alone is not a peer-reviewed journal DOI. SchGen's earlier under-review OpenReview manuscript is not evidence of acceptance.

## Identity and updates

Records have stable local IDs and sets of external identifiers. arXiv version suffixes and DOI URL/case variations are normalized. Shared external IDs merge automatically; otherwise exact normalized title, shared author and nearby year are required. Similar titles, Part I/II and fuzzy similarity do not suffice. This is conservative and intentionally leaves some cross-version duplicates for review.

Metadata provenance is a list of source/provider URLs. Reviewed text remains authoritative locally; API disagreements for title/year/venue are recorded as suggestions. Missing identifiers may be filled in later. Citation relations retain the provider. No assumption is made that publication year equals discovery year, arXiv revision year, or a year embedded in a DOI.

## Operational limits and completeness

The collector is serial. arXiv requests are spaced at least 3.1 seconds apart, other hosts at least 1.1 seconds. HTTP requests have timeouts, bounded exponential retries, Retry-After handling and a six-hour local cache. Rate-limited or broken sources report failures instead of empty successful results. Every query has a page cap and a cap hit is a warning. Independent jobs continue after a failure.

No system based on these sources can guarantee all PCB routing literature. Complete historical work requires hand checks of proceedings/journal tables of contents, alternate terminology, older digitized papers, and repeated citation expansion. The catalog is a maintained selection rather than a count of all papers in the field. Coverage can be audited by comparing a manually checked venue/year bibliography against discovery output; report precision/recall against that explicit reference set instead of claiming universal completeness.

## Source documentation

- [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html) and [API terms / rate limits](https://info.arxiv.org/help/api/tou.html).
- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) and [filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/).
- [Semantic Scholar API](https://www.semanticscholar.org/product/api), [Graph reference](https://api.semanticscholar.org/api-docs/graph) and [tutorial](https://www.semanticscholar.org/product/api/tutorial).

API availability, authentication and provider quotas can change; recheck these sources when deploying or troubleshooting. The collector implements three providers rather than assuming every scholarly API remains freely accessible without a key.
