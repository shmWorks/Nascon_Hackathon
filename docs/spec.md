# Spec — Personal Morning Paper (NaSCon'26)

Authoritative for objective, constraints, scope, acceptance cases and judge-evidence mapping. Exact organizer wording: [`brief.md`](brief.md) (PDF: [`brief.pdf`](brief.pdf)). On conflict, the brief wins; fix this file.

## Problem

News that matters to a reader is scattered across dozens of sites, apps and newsletters. They hop between them, click link after link, and still cannot name three things they learned. Aggregators and feeds (Google News, Feedly) collect links but leave selection, verification and synthesis to the reader, and infinite feeds never let them finish.

## Solution and value (E3)

One finite morning edition per reader, ready to read in about 10 minutes, on the web or as a newspaper-style PDF. A reader pays for four felt outcomes, each visible in the product:

| Felt outcome | Product evidence on screen |
| --- | --- |
| Time back: one place, then done | Finite edition with a "You're caught up" end state and "Three things to know" |
| Trust: no need to check the sources | Each story merges several sources; each claim shows its source and a verified quote; "N claims verified, M sources" |
| Relevance that visibly improves | "Why this story" per story; a profile page showing what the paper learned and from which actions |
| Calm control | One-tap skip, more/less like this, follow/mute; nothing changes after the edition is committed |

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
| Deployment, CI/CD, paid-grade value | Required (E1–E3) | User |
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
| E1 | Deployed and reachable by evaluators (user, 2026-10-17 16:45). |
| E2 | GitHub used throughout with regular commits pushed; CI/CD pipeline in place; evaluators check both (user). |
| E3 | Value a reader would pay for: tangible, felt value, not a feature demo (user). |

Reader actions named in the brief ("The idea"): read on web page, click through to original article, skip unwanted items, download whole paper as PDF.

## User stories

Priority maps to the plan in `state.md`: **M** must (M0-M3), **S** should (M4), **C** could (only after all M and S pass). Each story names the case that proves it.

| # | As a | I want | So that | P | Proof |
| --- | --- | --- | --- | --- | --- |
| U1 | new reader | to sign up with email and password | my paper and history are mine | M | A1 |
| U2 | new reader | to pick topics from chips and type interests in my own words in under 60 s | my first edition already fits me | M | A1, F5 |
| U3 | new reader | to rate a few real headlines during onboarding | the paper learns my taste before day one | C | A1 |
| U4 | reader | one edition each morning covering the previous 24 h | I read once and I am done | M | A2, A4 |
| U5 | reader | my most important story as the lead, then sections ordered by my interests | the layout itself reflects what I care about | M | A3 |
| U6 | reader | each story synthesized from all its sources, every claim quoted and cited | I can trust it without opening five tabs | M | Synthesis verification test |
| U7 | reader | to open the original article from any story | I can go deeper | M | A6 |
| U8 | reader | to skip a story with one tap | I see less of what I do not want | M | A7 |
| U9 | reader | more/less like this, and follow/mute on topics and sources | I steer the paper directly | M | A10 |
| U10 | reader | to download today's edition as a newspaper-style PDF | I can read it offline or print it | M | A2, A8 |
| U11 | reader | to open any previous edition | I can find what I read before | M | A9 |
| U12 | reader | to see why each story was chosen | I understand and trust the selection | S | UI walkthrough |
| U13 | reader | a profile page showing what the paper learned | I see it getting better | S | A10 |
| U14 | reader | "Three things to know" at the top | I leave with concrete takeaways | S | R5 |
| U15 | reader | a clear end state when I finish | I feel done, not pulled to scroll | S | UI walkthrough |
| U16 | reader | honest notices when sources or summaries are unavailable | I am never shown invented content | M | F1-F4, F6 |
| U17 | reader | labeled "Exploring" stories outside my usual topics | my paper does not become a bubble | C | UI walkthrough |
| U18 | evaluator | a deployed URL with three ready personas and 7 days of editions | I can judge the product without setup | M | E1, A3, A4 |
| U19 | evaluator | CI running tests on every push and deploying main | I can see engineering discipline | M | E2 |
| U20 | evaluator | evidence that learning works, against baselines | the learning claim is not hand-waving | S | A10 simulation report |

## Acceptance cases

Derived from brief text. Observable form is proposed; the user ratifies changes to it. Expected outcomes change only with an explicit reason recorded in `state.md`.

| ID | Req | Case | Pass when |
| --- | --- | --- | --- |
| A1 | R1 | New reader completes onboarding | Interests, free-text interests and calibration responses are persisted as events; the first edition's ranking is computed from them |
| A2 | R2 | Edition generated for a reader on a given day | A PDF is rendered at commit time and stored for that reader and date, with newspaper-inspired layout |
| A3 | R2 | Three readers with non-overlapping interests (demo personas) | Their editions differ in selected stories and presentation in line with their interests |
| A4 | R2, R3 | Daily freshness, 7-day window | For each day D−6…D, an edition is built only from items with source time in [D−1 06:00, D 06:00) PKT, using the profile as it stood that day, with that day's signals replayed before D+1; signals on backfilled days come from the persona simulator and are labeled "simulated reader". Days before today are labeled "backfilled"; today is "live". A real unattended next-day run is recorded as unverified |
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
| Topic | A labeled vector: an IPTC Media Topics node or a reader's free-text interest; items are assigned to nearest topics by embedding similarity; learning keeps one posterior per topic |
| Story | A cluster of items, across sources and modalities, about the same event; the unit that is ranked, synthesized and shown |
| Synthesis | One model output per story reasoning over all its items together; each claim cites item ids with a verbatim quote that code verifies against the item's text, and unverified claims are dropped |
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

## Implementation decisions

Components and data flow: [`README.md` Architecture](../README.md#architecture). Decision rationale: [`state.md` Decisions](state.md#decisions). Modules are built against these contracts.

- **Two choke points own all external effects.** Every model call goes through one LLM gateway: cache by input hash, per-model budgets, error-classified retry, model fallback, media validation. Every outbound HTTP request goes through one fetch gateway: cache, timeout, honest User-Agent, robots.txt, per-host pacing. No other module imports an HTTP or model client.
- **Pipeline entry points** (CLI and web call the same functions; all idempotent):
  - `run_day(day)`: shared stages for edition day `day` (ingest, allowlist, embed).
  - `build_edition(reader, day, kind)`: rank, cluster, select, retrieve, synthesize, commit, render; `kind` is live or backfilled.
  - `profile(reader, as_of)`: topic and source posteriors folded from events up to `as_of`.
  - `simulate_day(persona, edition)`: labeled simulated events for a backfilled edition.
- **Persistence (SQLite):** `readers`, `sessions`, `events` (append-only, `simulated` flag), `items` (url, domain, title, description, source time, image url, feed body, edition day, vector), `topics` (label, kind iptc or custom, owner reader or none, vector), `reader_topics` (prior), `editions` (reader, day, kind, status, stories JSON, PDF path; unique per reader and day).
- **Synthesis output contract:** `{headline, dek, claims: [{text, item_ids, quote}], image_note?}`. A claim survives only if its quote is found in a cited item's extracted text.
- **Deployment (E1) and CI/CD (E2):** one Docker image (Python + Playwright Chromium) serving the web app; GitHub Actions runs lint and tests on every push and deploys `main`. Host is an open decision in `state.md`.

## Testing decisions

- **Good test:** asserts observable behavior at a public seam (an edition's contents, an HTTP response, a downloaded file), never internal calls.
- **Seams (three, highest possible):**
  1. `build_edition` with fake LLM and fetch gateways replaying recorded responses: A2, A3, A5, F1-F3, F6, synthesis verification. Runs offline in CI with no key.
  2. Web app through an HTTP test client: A1, A6, A7, A9, F5, auth, Origin check.
  3. One browser test that clicks Download: A8.
- **Learning:** posterior-update unit tests plus the persona simulation (A10) against onboarding-only, recency and random baselines.
- **Falsify first:** each guard (quote verification, retrieval acceptance, media validation) gets a test that fails on the unguarded code.
- **Prior art:** `spikes/retrieval.py` swap test (negatives generated from real data, no hand labels).

## Out of scope

Payments and pricing, email verification and password reset, mobile apps, push or email delivery, real unattended overnight scheduling (simulated rollover only), Google News source, video and podcast stages, audio briefing, recall quiz, multi-language editions.

## Judge-evidence mapping

Official criteria and weights are undisclosed. Criteria below are **provisional**, taken from the brief's parts and the user's quality bar. Weights: unknown. Self-scores are not recorded.

| Criterion (provisional) / weight | Evidence required | Current proof | Gap / next action |
| --- | --- | --- | --- |
| R1 Onboarding / unknown | Browser walkthrough: new reader → first edition (A1) | Browser QA 18:05: sign-up → onboarding (chips + free text, F5 blocked) → edition built | Calibration step deferred (C) |
| R2 Personalized newspaper PDF / unknown | PDF artifact; two-reader comparison (A2–A4) | 21 PDFs for 3 personas x 7 days; per-reader masthead, lead, sections by interest | — |
| R3 Web reading experience / unknown | Browser walkthrough of A5–A9 | Browser QA: skip overlay, feedback, download, archive; same template for web and PDF | — |
| R4 Learning / unknown | Same-reader before/after editions (A10) | Persona simulation nDCG@10 beats onboarding-only for 3/3 personas (state.md) | Real-reader evidence impossible before deadline |
| R5 Exploration / unknown | Demoed feature beyond core | None | Only after R1–R4 have proof |
| End-to-end MVP completeness / unknown | Fresh-terminal run: onboarding → edition → PDF → signal → next edition | Local run end to end; CI green | Deployed run |
| Deployed, CI/CD, paid-grade value / required (E1-E3) | Live URL; green CI run on `main`; felt-outcome evidence on screen (Solution table) | None | Host decision; Dockerfile; workflow |
| Fit for Eynvision / unknown | Proposed evidence: usable workflow, source traceability, matched editions and observable adaptation; rationale: [sponsor research](eynvision.md) | Public-source research complete; no product proof | Validate R1–R4 first; sponsor patterns guide tradeoffs, not official scoring |
