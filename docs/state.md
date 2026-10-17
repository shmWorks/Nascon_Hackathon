# State

Authoritative for verified status, blockers, next action and consequential decisions. Update when a milestone passes or fails, a blocker changes, a decision changes, or work is handed off. Requirement IDs (R*, A*) refer to [`spec.md`](spec.md).

Last updated: 2026-10-17 11:05 PKT. Code freeze 20:00 PKT; deadline 21:00 PKT.

## Verified status

- Brief extracted: [`brief.md`](brief.md) (verbatim) and [`spec.md`](spec.md) (requirements, acceptance cases, provisional judge mapping).
- No code. No stack, base repository or architecture chosen.
- `README.md` not yet created; it arrives with the first runnable command.
- Eynvision public-source research and adversarial review complete: [agent brief](eynvision.md), [source provenance and limits](eynvision.provenance.md). No product behavior verified by this research.

## Blockers and open questions

- Official rubric/weights and named NaSCon'26 judges remain unverified. Sponsor-fit evidence is proposed in `spec.md`; research recommendations are not added acceptance gates.

## Next action

Handoff §2, steps 2–4:

1. Define the primary task, simplest baseline, and observable success/failure cases; add failure-behavior acceptance cases to `spec.md`. In the same pass, ratify or reject the acceptance proposals in [`eynvision.md` § Execution priorities](eynvision.md#execution-priorities): skip as reading overlay (A5/A7), explicit topic feedback for A10, simulated date rollover for A4 (real next-day run is unverifiable before the deadline), failure cases.
2. Test the dependencies most likely to block delivery: article source access across the web, model access, PDF rendering.
3. Select a base (or none), record commit and license, pass the base validation gate (handoff §2) within 45 minutes.
4. Propose a time-boxed schedule to 20:00 freeze for user approval.

## Decisions

`Decision | Reason | Consequence | Reconsider when`

- Brief moved to `docs/brief.pdf` plus verbatim `docs/brief.md` | Original filename (apostrophe, spaces) breaks unquoted shell commands; markdown is greppable and cheap to load | Agents read `brief.md`, not the PDF | Organizer issues a revised brief
- Defer `README.md` | Every required section would be empty | No README until a stack exists | First runnable command exists
- `CLAUDE.md` only imports `AGENTS.md` | One home for shared agent rules across Claude Code and Codex | Edit rules in `AGENTS.md` only | Clients diverge in needed instructions
- Python FastAPI + server-rendered Jinja + SQLite; no frontend build; no LangGraph | One template renders web and PDF, so A5 holds by construction; fixed pipeline needs no agent framework | UX quality must come from design, not a component framework (see UX decision, pending) | A required interaction cannot be built without a client framework
- Committed edition is immutable; skip is a web-only reading overlay plus a stored event | Preserves edition identity for PDF and archive (eynvision.md priority 4) | PDF and archive always show the full committed edition | Readers need a "skipped-removed" PDF
- PDF: Playwright Chromium renders the same Jinja template with print CSS; acceptance verified by clicking the web Download control | Chromium already installed; WeasyPrint needs GTK on Windows; one layout source | Chromium is a runtime dependency | Render time or install footprint blocks the demo
- Error-classified retry policy (spec.md § Failure cases) | Blanket retries waste quota on permanent errors and hide config faults | Each error class has a defined action | A provider returns errors outside the classes
- Presentation personalization: section order by interest strength, lead story = top-ranked with long summary, briefs below; longer brief summaries are a later add-on | Brief R2 requires personalized presentation, not only selection | Layout depends on ranking output | —
- R5: "Three things to know" front-page box now; audio briefing and recall quiz only if A1–A10 have proof | Directly answers the brief's "can't name three things they learned" | One extra model output per edition | —
- Localhost only; repo stays private until the user makes it public before submission, after a secret scan | Loom is the demo; S1 requires public repo | No deployment work | Judges require a live URL
- 7-day backfill: one edition per day D−6…D from that day's real items, profile and signals replayed in order | Gives a real archive (A9), dated freshness (A4) and visible learning across 7 editions (A10) | Sources must support date-scoped retrieval; RSS is not required | A source spike shows a day cannot be reconstructed
- Multimodal Story synthesis: cluster items across sources and modalities into a Story; one model call reasons across all of a story's items together, with per-claim citations, agreement/disagreement, and what visuals add. Stages: text+image → YouTube video → podcast audio | Differentiator: one story, all angles, every claim traceable, versus link lists | Model must accept mixed modalities; clustering needs embeddings | Provider cannot accept images or quota cannot cover synthesis
- UX: finite daily edition with a "caught up" end state; daily ritual is the habit loop; UX principles derived from the reader's job, then multi-expert design review before build | Brief's failure metric is "can't name three things learned", so comprehension and trust beat time-on-site | No infinite feed | Readers want continuous browsing beyond the edition
- Onboarding is designed as preference elicitation, not a form: topic chips + free text + calibration on real headlines chosen to maximize information about uncertain interests | The onboarding seed sets the learning prior; downstream ranking quality depends on it | Onboarding needs today's items before it can calibrate | Calibration adds friction beyond ~60 s
- Thin auth: email + argon2id password, server-side sessions, HttpOnly SameSite=Lax cookie, CSRF tokens, login rate limit; append-only event log is the source of truth, profile is derived | Brief needs per-reader persistence; raw events enable learning replay and audit | No email verification or password reset (recorded limitation) | Deployment beyond localhost
- Three demo personas: AI product builder; cricket + space science; climate + global markets | Three non-overlapping readers show a pattern, not a coincidence | Seeded via the real onboarding flow | —
- PDF rendered once at edition commit and stored; Download serves the stored file; F4 retry re-renders | Same artifact every time; fast download | Storage per edition | —
- Learning: one binary engagement event per seen impression (click-through without quick bounce, dwell ≥ τ from the reader's own dwell distribution, save, or "more like this" = 1; seen without action, skip, "less like this" = 0); Beta-Bernoulli posterior per topic and per source; onboarding prior α₀=m·n, β₀=(1−m)·n; daily decay toward prior with half-life h; score = topic posterior mean × clipped source factor; mute/follow are rules; k exploring slots by Thompson sampling seeded by hash(date, reader). Initial n=4, m=0.3/0.1, h=14 d, k=2 of ~15, clip [0.5, 2] are assumptions tuned in a persona simulation | Signal strength emerges from counts instead of hand-set weights; position bias handled by counting only seen impressions; exploration counters filter bubbles. Sources: Yi et al. RecSys 2014; Joachims et al. SIGIR 2005; Chapelle & Li NIPS 2011; Liu et al. IUI 2010; Chaney et al. RecSys 2018 | Requires viewport impression tracking; simulation proves code learns under its own assumptions, not real-reader value | LinUCB if features beyond topic and source are added
- Sponsor portfolio informs quality tradeoffs, not a product pivot | Public evidence supports practical AI workflows but establishes no internal news-tool demand or private rubric | Preserve R1–R4; validate proposed semantics before changing acceptance cases | Organizer provides new requirements or sponsor/user validation changes the target
