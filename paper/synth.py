"""Story synthesis with code-verified citations, and "Three things to know".

A claim survives only if its quote is found (whitespace/case-normalized) in the extracted text of a cited item.
"""
import re

from pydantic import BaseModel

from . import llm

MAX_ITEM_CHARS = 6000


class Claim(BaseModel):
    text: str
    item_ids: list[int]
    quote: str


class Synthesis(BaseModel):
    headline: str
    dek: str
    claims: list[Claim]
    image_note: str


class Things(BaseModel):
    things: list[str]


def _norm(s):
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def verify(claims, texts: dict[int, str]):
    """Keep claims whose quote occurs in a cited item's text. Pure function: tested directly."""
    kept = []
    for c in claims:
        q = _norm(c["quote"])
        if len(q.split()) < 4:
            continue  # too short to prove anything
        if any(q in _norm(texts.get(i, "")) for i in c["item_ids"]):
            kept.append(c)
    return kept


PROMPT = """You are the editor of a reader's personal morning paper. Write ONE story from the sources below, which all
cover the same event. Reason across all sources (and the image if present) as one system: what happened, why it
matters, where sources agree or differ.

Rules:
- Use only facts stated in the source texts. Ignore site navigation, ads and lists of other articles.
- headline: max 12 words. dek: one sentence, max 30 words.
- claims: 3-6 key facts. Each claim cites the source ids it comes from and includes a quote copied EXACTLY,
  verbatim, 6-25 words, from one cited source.
- image_note: what the image shows that the text does not, or "" if no image or nothing to add.

Sources:
{sources}
"""


def synthesize(story_items, texts: dict[int, str], image=None, role="synth"):
    sources = "\n\n".join(f"[{k}] {it['domain']} — {it['title']}\n{texts[k][:MAX_ITEM_CHARS]}" for k, it in enumerate(story_items) if texts.get(k))
    out = llm.generate_json(role, PROMPT.format(sources=sources), Synthesis, images=[image] if image else [])
    total = len(out.get("claims", []))
    out["claims"] = verify(out.get("claims", []), texts)
    out["claims_total"] = total
    if not image:
        out["image_note"] = ""
    return out


def three_things(headlines_and_deks: list[str]):
    prompt = ("From today's stories below, write the three things this reader should know, one short sentence each, "
              "each grounded only in the given text.\n\n" + "\n".join(f"- {h}" for h in headlines_and_deks))
    return llm.generate_json("synth", prompt, Things).get("things", [])[:3]
