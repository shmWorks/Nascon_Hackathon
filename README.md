# Morning Paper

A personal daily newspaper: it learns what each reader cares about, gathers the day's stories from across the web, synthesizes each story from all its sources with verified citations, and delivers one finite edition as a web page and a newspaper-style PDF. Built for NaSCon'26 ([brief](docs/brief.md), [spec](docs/spec.md)).

## Setup

```bash
uv sync
uv run playwright install chromium
cp .env.example .env   # then set GEMINI_API_KEY
```

## Commands

| Task | Command |
| --- | --- |
| Create DB and load topics | `uv run python -m paper init` |
| Shared stages for a day (ingest, allowlist, embed) | `uv run python -m paper run-day --day 2026-10-17` |
| Build one reader's edition | `uv run python -m paper build --reader 2 --day 2026-10-17` |
| Seed 3 personas + 7 days of editions with simulated reading | `uv run python -m paper demo --days 7` |
| Learning evaluation vs baselines (A10) | `uv run python -m paper evaluate` |
| Export demo data for deployment | `uv run python -m paper export-demo` |
| Run the web app | `uv run uvicorn paper.web:app --port 8000` |
| Tests (offline, no API key) | `uv run pytest -q` |
| Lint | `uv run ruff check paper tests` |

Demo readers: `ayesha@demo.paper`, `bilal@demo.paper`, `sara@demo.paper`, password `morningpaper`.

## Deployment and CI/CD

- **CI** (`.github/workflows/ci.yml`): every push runs `ruff` and `pytest`; on `main`, a green run triggers the Render deploy hook (`RENDER_DEPLOY_HOOK` secret). Deploys never bypass tests.
- **Host:** Render free web service from the `Dockerfile`. The embedding model is baked into the image. The free disk is ephemeral, so `demo_data/` (personas, editions, PDFs, latest day's items) ships in the image; sign-ups made on the live site reset on restart.
- **Server PDFs:** the image has no Chromium (free tier has 512 MB RAM); demo PDFs are pre-rendered. A new reader's live edition shows the honest "PDF not available" notice with a retry (F4).


## Architecture

### Principles

1. **Staged batch pipeline, stored artifacts.** Each stage reads the previous stage's stored output and writes its own. Every stage is idempotent and resumable; a crash or quota stop resumes, it does not restart.
2. **External calls are content-addressed and cached.** Fetches, embeddings and model outputs are keyed by input hash under `data/cache/`. No external call is ever paid twice; reruns and the 7-day backfill are cheap.
3. **Shared work is done once per day, not per reader.** Ingestion, embedding, topic assignment, article retrieval and story synthesis are shared; only ranking, selection and edition commit are per reader.
4. **Models propose, code decides.** Embeddings and the LLM produce vectors and text. Ranking, thresholds, citation verification, learning and state transitions are deterministic code.
5. **Committed state is immutable; learning state is derived.** Editions never change after commit. The reader profile is a fold over the append-only event log and can be recomputed at any time.

### Data flow

```text
                 shared, per edition day D                          per reader R, day D
GKG files + RSS ─► ingest ─► allowlist ─► embed ───────────┐
                                                            ├─► rank ─► cluster ─► select ─► retrieve ─► synthesize ─► commit ─► render web + PDF
reader topics + profile (fold of event log) ────────────────┘                                  (shared cache)  (shared cache)
                                                                                                                         │
web UI: onboarding, edition, archive, download ──► events (impressions, clicks, dwell, skip, feedback) ──► event log ─────┘
```

### Components

| Component | Responsibility | Key rule |
| --- | --- | --- |
| `ingest` | Pull GDELT GKG files (every 3 h in the window) and the RSS catalog into `items` | Edition day D = source time in [D−1 06:00, D 06:00) PKT |
| `allowlist` | Keep items from trusted domains | Domain qualifies by catalog membership, or by appearing on several days with articles that pass the retrieval check |
| `embed` | One embedding per item title+description (`gemini-embedding-2`, 256 dims) | Batched; cached by text hash; lexical fallback if quota is exhausted |
| `topics` | Topic vectors, not a pipeline stage | A topic is a labeled vector: an IPTC Media Topics node or a reader's free-text interest. Item–topic similarity is computed from stored vectors at rank time, so a topic added later applies to all items |
| `rank` | Score candidates per reader | score = source factor × Σ over the reader's topics with cosine ≥ τ_rel of w(item, t) · E[θ_t], w = normalized similarity; τ_rel calibrated on real items; mutes remove; follows raise the prior |
| `cluster` | Group candidate items about the same event into stories | Embedding cosine threshold within the reader's candidate set |
| `select` | Choose the edition's ~12 stories | Top by score, cap per topic, k exploring slots by Thompson sampling seeded by hash(date, reader) |
| `retrieve` | Get article text for selected items | Generic chain: feed body → direct fetch → Jina Reader → Wayback; accept only text that passes the title-match + length check |
| `synthesize` | One grounded synthesis per story over all its items (text + validated image); cached by item-set hash | Claims carry item ids + a verbatim quote; code drops claims whose quote is not in the cited item's text |
| `commit` | Freeze the edition, add "Three things to know", render HTML and PDF | Edition, layout and PDF stored once; PDF via Playwright Chromium from the same template |
| `web` | Auth, onboarding, edition reading, archive, download, event capture | Skip is a view overlay; impressions count only when ≥50% visible for ≥1 s |
| `learn` | Fold events into Beta posteriors per topic and source | One binary engagement outcome per seen impression, credited to topics by the same weights w used in ranking; daily decay toward the onboarding prior |
| `simulate` | Persona readers with known true interests | Generates labeled simulated events for backfilled days; same truth yields the A10 evaluation |

### State and persistence

| Store | Contents | Lifetime |
| --- | --- | --- |
| `data/paper.db` (SQLite) | readers, sessions, events (append-only), items, item topics, editions, edition stories | Durable; source of truth |
| `data/cache/` | Raw GKG/RSS files, fetched pages, embeddings, model outputs, keyed by input hash | Durable; safe to delete (costs quota to rebuild) |
| `data/editions/` | Rendered PDF per reader and date | Durable; regenerable from the committed edition |

### External dependencies and failure behavior

| Dependency | Use | On failure |
| --- | --- | --- |
| GDELT GKG raw files | Across-the-web candidate pool, any past day | Skip missing files; F1/F2 |
| Publisher RSS | Today's items, feed bodies, niche depth | Skip feed; F1 |
| Jina Reader (keyless, ≤20 RPM) | Article text when direct fetch fails | Next route; item marked "not readable" |
| Wayback Machine | Last-resort article copy | Item marked "not readable" |
| Gemini API free tier | Embeddings, synthesis, three-things | Error-classified retry ([spec § Failure cases](docs/spec.md#failure-cases)); model fallback within Gemini; F3 |
| Playwright Chromium | PDF render | F4: web edition stays; retry control |

Only public news text and interest phrases go to the Gemini free tier; never names, emails or event logs.

## Attribution

- IPTC Media Topics, CC BY 4.0, IPTC.
- GDELT Project data.
- Article extraction: trafilatura (Apache-2.0).
