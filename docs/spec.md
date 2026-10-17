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
| A1 | R1 | New reader completes onboarding | Interests are persisted and the first edition is built from them |
| A2 | R2 | Edition generated for a reader on a given day | A PDF exists for that reader and date, with newspaper-inspired layout |
| A3 | R2 | Two readers with different interests | Their editions differ in selected content and/or presentation in line with their interests |
| A4 | R2, R3 | Daily freshness | Next day's edition is a new edition built from articles gathered that day |
| A5 | R3 | Web edition vs PDF | Both show the same edition (same articles) |
| A6 | R3 | Reader clicks an article | Original article URL opens |
| A7 | R3 | Reader skips an article | Article is removed or hidden from the reading view; skip is recorded |
| A8 | R3 | Reader downloads PDF from web page | PDF of the current edition downloads |
| A9 | R3 | Reader opens archive | Previous editions are listed and open |
| A10 | R4 | Reader generates signals (clicks, skips, others chosen at design) | A later edition reflects them, shown by a same-reader before/after comparison |

Failure behavior (handoff §9: missing input, source/model failure, out-of-scope input) gets acceptance cases once the pipeline is designed.

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
| Fit for Eynvision / unknown | To be defined from user's Eynvision research | None | User researching |
