"""Single home for every tunable value. Each value states its meaning; none is site-specific."""
import os
from datetime import timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PAPER_DATA", ROOT / "data"))
DB_PATH = DATA / "paper.db"
CACHE = DATA / "cache"
EDITIONS = DATA / "editions"

PKT = timezone(timedelta(hours=5))
EDITION_CUTOFF_HOUR = 6  # edition D covers source time in [D-1 06:00, D 06:00) PKT (D4)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODELS = {  # per-model free budgets (state.md: model routing)
    "synth": ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemma-4-26b-a4b-it", "gemini-3-flash-preview"],
    "lead": ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"],
    "embed": "gemini-embedding-2",
}
EMBED_DIM = 256          # gemini-embedding-2 supports 128-3072; 256 keeps storage small
EMBED_BATCH = 100        # texts per embedding request
LLM_MAX_ATTEMPTS = 3     # transient-error attempts per model before falling back
LLM_CALL_BUDGET_S = 60   # wall-clock budget per logical call across retries

USER_AGENT = "MorningPaperBot/0.1 (+https://github.com/shmWorks/Nascon_Hackathon)"
FETCH_TIMEOUT_S = 8
JINA_MIN_INTERVAL_S = 3.1  # keyless Jina Reader limit is 20 RPM (jina.ai/reader)
RETRIEVE_MIN_WORDS = 120   # shorter text is a stub/teaser/error page, not an article body
RETRIEVE_MIN_TITLE_RECALL = 0.5  # share of title content-words that must appear in the body

GKG_STEP_HOURS = 3         # sample one GKG 15-minute file every 3 h of the edition window
CANDIDATES_PER_READER = 80
EDITION_SIZE = 12
EXPLORE_SLOTS = 2
MAX_PER_TOPIC = 4
CLUSTER_COSINE = 0.80      # items above this title-embedding similarity describe the same event
RELEVANCE_COSINE = 0.30    # item-topic similarity below this contributes nothing (calibrate on data)

# Learning (state.md: learning mechanism). Assumptions tuned by the persona simulation.
PRIOR_STRENGTH = 4.0
PRIOR_MEAN_CHOSEN = 0.3
PRIOR_MEAN_OTHER = 0.1
DECAY_HALF_LIFE_DAYS = 14.0
SOURCE_FACTOR_CLIP = (0.5, 2.0)

for d in (DATA, CACHE, EDITIONS):
    d.mkdir(parents=True, exist_ok=True)
