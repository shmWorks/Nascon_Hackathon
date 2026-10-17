"""Spike: Gemini free-tier access, structured output, multimodal input, embeddings, latency, error shape."""
import json
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


class Tag(BaseModel):
    idx: int
    topics: list[str]


class Synthesis(BaseModel):
    headline: str
    summary: str
    image_adds: str
    cited_item_ids: list[int]


def run(name, fn):
    t0 = time.perf_counter()
    try:
        out = fn()
        print(f"[OK] {name} {time.perf_counter() - t0:.1f}s ->", out)
    except Exception as e:
        print(f"[ERR] {name} {time.perf_counter() - t0:.1f}s {type(e).__name__}: {str(e)[:600]}")


titles = ["India beat Australia by 5 wickets in Perth Test", "NASA's Europa Clipper completes Mars flyby", "OpenAI releases new reasoning model for agents", "Oil prices fall as OPEC raises output"]


def tag():
    r = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Assign 1-2 topics from [cricket, space, ai, markets, climate, other] to each headline:\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(titles)),
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=list[Tag]),
    )
    return r.text, r.usage_metadata.total_token_count


img = httpx.get("https://ichef.bbci.co.uk/news/1024/branded_news/6b8e/live/placeholder.jpg", follow_redirects=True)
if img.status_code != 200 or not img.headers.get("content-type", "").startswith("image"):
    img = httpx.get("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Europa-moon-with-margins.jpg/480px-Europa-moon-with-margins.jpg", headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)


def synth():
    r = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=img.content, mime_type=img.headers["content-type"].split(";")[0]),
            "Item 1 (text): NASA's Europa Clipper is on its way to Jupiter's moon Europa to study its ice shell. Item 2 (image above): lead image from the same story. "
            "Write one grounded synthesis; image_adds = what the image shows that the text does not; cite item ids.",
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Synthesis),
    )
    return json.loads(r.text), r.usage_metadata.total_token_count


def embed():
    r = client.models.embed_content(model="gemini-embedding-2", contents=titles[:2])
    return [len(e.values) for e in r.embeddings]


for name in ["gemini-3.8-flash", "gemini-3.6-flash", "gemma-4"]:
    pass  # availability probed only via models.list to avoid spending quota

run("tag 3.1-flash-lite json", tag)
run(f"synth 3.5-flash-lite image({img.status_code},{len(img.content)}B)", synth)
run("embed gemini-embedding-2", embed)
run("list models", lambda: sorted(m.name.split("/")[-1] for m in client.models.list() if any(k in m.name for k in ("flash", "gemma", "embedding"))))
