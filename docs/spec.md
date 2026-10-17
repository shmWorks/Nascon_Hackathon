# Spec — Personal Morning Paper (NaSCon'26)

Authoritative for objective, constraints, scope, acceptance cases and judge-evidence mapping. Exact organizer wording: [`brief.md`](brief.md) (PDF: [`brief.pdf`](brief.pdf)). On conflict, the brief wins; fix this file.

## Objective

A product that learns what each reader cares about, gathers matching articles from across the web every day, and delivers one personal morning paper: read on the web, click through to originals, skip items, download as a newspaper-style PDF.

## Constraints

| Item | Value | Source |
| --- | --- | --- |
| Hard deadline | 2026-10-17 21:00 PKT | User |
| Internal code freeze | 2026-10-17 20:00 PKT — remaining hour is for Loom video, architecture diagram, submission | User |
| Team | Solo (Sheraz Malik), with Claude Code and, when needed, Codex | User |
| Rubric / weights | Undisclosed by organizer | User, brief |
| Quality bar | Complete end-to-end MVP, desirable and usable to the standard of the sponsor and judge, Eynvision (software house) | User |
| Repo | Public GitHub repo; all commits monitored | Brief (G1) |
| Reuse restrictions | Not stated in brief | Brief |
| Stack preference | React/TypeScript, Python, SQL, Gemini, LangGraph — preference, not mandate | Handoff §1 |

Use the system clock for schedule decisions (`date`); timezone is PKT (UTC+5).

## Requirements

IDs are stable; reference them in commits, tests and `state.md`.

| ID | Requirement (condensed from brief) |
| --- | --- |
| R1 | Onboarding captures enough of the reader's interests to personalize the paper, with a great user experience. |
| R2 | A daily PDF, made fresh every day, inspired by traditional newspaper structure and layout; content selection and presentation personalized to the reader. |
| R3 | The same edition as a complete reading experience on the web page; downloadable as that PDF; previous papers accessible. |
| R4 | The product improves its understanding of the reader over time from usage signals and uses it to improve future papers. Signal capture and interpretation are open. |
| R5 | Optional exploration beyond the core: non-news content, new discovery modes, unexpected AI uses, unspecified experiences. |
| G1 | Own GitHub repo created at hackathon start; all commits monitored. |
| S1 | Submit public GitHub repo link. |
| S2 | Submit Loom video of the product, 5 minutes max. |
| S3 | Submit architecture design diagram. |

Reader actions named in the brief ("The idea"): read on web page, click through to original article, skip unwanted items, download whole paper as PDF.

## Acceptance cases

Derived from brief text. Observable form is proposed; the user ratifies changes to it. Expected outcomes change only with an explicit reason recorded in `state.md`.

| ID | Req | Case | Pass when |
| --- | --- | --- | --- |
| A1 | R1 | New reader completes onboarding | Interests, free-text interests and calibration responses are persisted as events; the first edition's ranking is computed from them |
| A2 | R2 | Edition generated for a reader on a given day | A PDF is rendered at commit time and stored for that reader and date, with newspaper-inspired layout |
| A3 | R2 | Three readers with non-overlapping interests (demo personas) | Their editions differ in selected stories and presentation in line with their interests |
| A4 | R2, R3 | Daily freshness, 7-day window | For each day D−6…D, an edition is built only from items published that day, using the profile as it stood that day, with that day's signals replayed before D+1. Days before today are labeled "backfilled"; today is "live". A real unattended next-day run is recorded as unverified |
| A5 | R3 | Web edition vs PDF | Both render the same committed edition (same stories); web skips do not alter the PDF or archive |
| A6 | R3 | Reader clicks an article | Original article URL opens |
| A7 | R3 | Reader skips an article | Story is hidden from the web reading view only (overlay); skip is stored as an event; the committed edition is unchanged |
| A8 | R3 | Reader downloads PDF from web page | Clicking the web page's Download control yields the PDF of the current edition; verified by a browser test that clicks that control, as a reader would |
| A9 | R3 | Reader opens archive | Previous editions are listed and open |
| A10 | R4 | Reader generates engagement events | A later edition reflects the updated posteriors (state.md § Decisions, learning mechanism), shown by a same-reader before/after comparison on controlled candidates; persona simulation reports nDCG@10 against onboarding-only, recency and random baselines |

## Glossary

Canonical terms; use them in code, UI copy and docs.

| Term | Meaning |
| --- | --- |
| Reader | An authenticated account with its own profile and event log |
| Item | One ingested piece of content from one source: article, image, video or audio, with publisher, URL and publication time |
| Story | A cluster of items, across sources and modalities, about the same event; the unit that is ranked, synthesized and shown |
| Synthesis | One model output per story reasoning over all its items together, with per-claim citations to items |
| Edition | The committed, immutable set of stories for one reader and one date, rendered as web page and PDF |
| Live / backfilled edition | Built on its own date / built today from items published on a past date |
| Impression | A story shown in an edition; **seen** when ≥50% of it was in the viewport for ≥1 s |
| Engagement event | Binary outcome per seen impression (1 = engaged, 0 = not), the only input to learning |
| Skip | Web-only reading overlay that hides a story; stored as an event; never alters the edition |
| Exploring slot | An edition slot filled by Thompson sampling to test uncertain interests; labeled in the UI |
| Profile | Derived state (topic and source posteriors, follows, mutes), recomputable from the event log |

### Failure cases

Ratified 2026-10-17. No case may produce fabricated text, a mislabeled stale edition, or an endless spinner.

| ID | Case | Pass when |
| --- | --- | --- |
| F1 | One source fails or exceeds its fetch timeout | Source is skipped; edition builds from the rest; reader sees "N sources unavailable" |
| F2 | All sources fail | No new edition is committed; last successful edition is shown with its own date and a banner |
| F3 | Model call fails or returns invalid output | Handled per the retry policy below; on exhaustion, story falls back to keyword topics + feed snippet labeled "summary unavailable" |
| F4 | PDF render fails | Web edition stays available; reader sees an error and a retry control |
| F5 | Onboarding submitted with no interests | Submission is blocked with a stated reason |
| F6 | An interest has no matching items | Section shows "No stories today for X"; no filler |

**Retry policy (F1, F3).** Classify by the actual error, not by a blanket retry count:

| Error class | Examples | Action |
| --- | --- | --- |
| Transient | HTTP 429, 500, 502, 503, 504, timeout, connection reset | Exponential backoff with full jitter; honor `Retry-After`; max 3 attempts within a per-call time budget; then next provider in the fallback chain, then F3 fallback |
| Invalid output | Unparseable JSON, schema-validation failure | One repair retry that feeds the validation error back to the model; then F3 fallback |
| Permanent request error | HTTP 400, content blocked by safety filter | No retry; F3 fallback for that item; log the reason |
| Configuration error | HTTP 401, 403, missing key, unknown model | No retry; fail fast; surface a setup error naming the variable or model |
| Unknown | Anything unclassified | One retry; then treat as permanent; log full error for classification |

Exact budgets (attempts, seconds, tokens) live in code configuration and are recorded in `README.md` once set.

## Judge-evidence mapping

Official criteria and weights are undisclosed. Criteria below are **provisional**, taken from the brief's parts and the user's quality bar. Weights: unknown. Self-scores are not recorded.

| Criterion (provisional) / weight | Evidence required | Current proof | Gap / next action |
| --- | --- | --- | --- |
| R1 Onboarding / unknown | Browser walkthrough: new reader → first edition (A1) | None | Design onboarding |
| R2 Personalized newspaper PDF / unknown | PDF artifact; two-reader comparison (A2–A4) | None | Choose PDF rendering path; test it early |
| R3 Web reading experience / unknown | Browser walkthrough of A5–A9 | None | Build after first vertical slice |
| R4 Learning / unknown | Same-reader before/after editions (A10) | None | Define signals and update rule |
| R5 Exploration / unknown | Demoed feature beyond core | None | Only after R1–R4 have proof |
| End-to-end MVP completeness / unknown | Fresh-terminal run: onboarding → edition → PDF → signal → next edition | None | First vertical slice |
| Fit for Eynvision / unknown | Proposed evidence: usable workflow, source traceability, matched editions and observable adaptation; rationale: [sponsor research](eynvision.md) | Public-source research complete; no product proof | Validate R1–R4 first; sponsor patterns guide tradeoffs, not official scoring |
