"""Live QA + demo recording against the deployed app.

1. Narration per scene -> neural TTS (edge-tts) with word timestamps.
2. Playwright drives real user flows for three personas; every step asserts what it shows (QA).
   Each scene is held for at least its narration length; actual scene start times are measured.
3. ffmpeg places each narration at its measured scene start; captions are built from the TTS word
   timestamps at the same offsets, so audio and captions share one clock by construction.
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import edge_tts
from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get("DEMO_URL", "https://morning-paper.onrender.com")
PASSWORD = "morningpaper"  # demo personas' published password (paper/personas.py)
VOICE = "en-US-AndrewMultilingualNeural"
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
ROOT = Path(__file__).resolve().parent.parent

SCENES = [
    ("intro", "News is scattered across dozens of sites. People click link after link, and still can't name three things they learned. Morning Paper fixes that. Every morning it reads the web for you, and prints one finite, personal newspaper. Let's see it live."),
    ("sara_login", "This is Sara. She follows climate, energy and markets. She signs in, and today's paper is waiting for her."),
    ("sara_top", "The masthead carries her name and today's date. At the top: three things to know, the takeaways she should leave with. The lead is the story most relevant to her."),
    ("sara_claims", "Every story is written from all the sources covering the same event. Each claim shows its source and a verbatim quote, and our code checks that the quote really appears in the cited article. Anything unverified is dropped, never invented."),
    ("sara_scroll", "Sections are ordered by what Sara cares about most. Each story says why it was chosen, and exploring stories test interests she hasn't mentioned, so the paper never becomes a bubble. Then she is done: a clear end, not an endless feed."),
    ("sara_learn", "She taps more like this on a story she enjoyed, and skips one she doesn't want. Every story she actually sees, and how she reacts, updates what the paper knows about her. Here is what it learned: where each topic started, and where her reading has taken it."),
    ("sara_archive", "Every past edition stays in her archive. And any edition downloads as a newspaper-style PDF: the same edition she reads on the web, ready to print or read offline."),
    ("ayesha", "Ayesha is an AI product builder. Same day, a completely different paper: AI, startups, and the technology industry."),
    ("bilal", "Bilal follows cricket and space. His paper leads with what he cares about. Three readers, three papers, from the same system."),
    ("onboarding", "A new reader signs up, picks topics grouped so they're quick to scan, and adds interests in their own words. Their first edition is printed in about two minutes."),
    ("architecture", "Under the hood, a shared daily pipeline ingests the whole web through GDELT and publisher feeds, embeds everything locally, and builds each reader's edition. Every model and web call goes through a gateway with caching, retries, and quota failover. Learning is a Bayesian model of each reader, and in simulation it beats onboarding alone, recency, and random ranking for all three readers."),
    ("close", "Every change is tested in C I before it deploys. Morning Paper: one paper, ten minutes, then you're done."),
]


async def _tts(name, text):
    c = edge_tts.Communicate(text, VOICE, rate="+4%", boundary="WordBoundary")
    audio, words = b"", []
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    (OUT / f"{name}.mp3").write_bytes(audio)
    return words


def narration():
    meta = {}
    for name, text in SCENES:
        words = asyncio.run(_tts(name, text))
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(OUT / f"{name}.mp3")]))
        meta[name] = {"words": words, "duration": dur}
    (OUT / "narration.json").write_text(json.dumps(meta))
    return meta


def record(meta):
    starts, qa = {}, []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(OUT / "video"), record_video_size={"width": 1280, "height": 720}, accept_downloads=True)
        page = ctx.new_page()
        t0 = time.monotonic()
        page.set_default_timeout(90000)

        def scene(name, fn):
            starts[name] = time.monotonic() - t0
            try:
                fn()
                qa.append((name, "pass", ""))
            except Exception as e:  # noqa: BLE001 — QA records the failure and keeps recording
                qa.append((name, "FAIL", str(e)[:300]))
            left = meta[name]["duration"] + 0.5 - (time.monotonic() - t0 - starts[name])
            if left > 0:
                page.wait_for_timeout(int(left * 1000))

        def smooth_scroll(px, steps=12, pause=120):
            for _ in range(steps):
                page.mouse.wheel(0, px / steps)
                page.wait_for_timeout(pause)

        def login(email):
            page.goto(f"{BASE}/logout")
            page.goto(f"{BASE}/login")
            page.fill("#email", email)
            page.fill("#password", PASSWORD)
            page.click("button[type=submit]")
            expect(page.locator("h1")).to_contain_text("Morning")

        scene("intro", lambda: (page.goto(BASE), expect(page.locator("h1")).to_contain_text("One paper"), page.wait_for_timeout(2500), smooth_scroll(500)))
        scene("sara_login", lambda: login("sara@demo.paper"))

        def sara_top():
            expect(page.locator(".things li")).to_have_count(3)
            page.locator(".things").scroll_into_view_if_needed()

        scene("sara_top", sara_top)

        def sara_claims():
            story = page.locator("article:has(.trust)").first  # a story with verified claims
            story.scroll_into_view_if_needed()
            expect(story.locator(".trust")).to_contain_text("claims verified")
            story.locator(".claims li").first.hover()

        scene("sara_claims", sara_claims)

        def sara_scroll():
            expect(page.locator(".section-head").first).to_be_visible()
            smooth_scroll(2600, steps=26, pause=260)
            page.locator(".done").scroll_into_view_if_needed()
            expect(page.locator(".done")).to_contain_text("caught up")

        scene("sara_scroll", sara_scroll)

        def sara_learn():
            page.evaluate("window.scrollTo(0,0)")
            first = page.locator("article[data-idx]").nth(1)
            first.scroll_into_view_if_needed()
            first.locator("[data-act=more]").click()
            expect(first.locator("[data-act=more]")).to_have_text("Noted")
            second = page.locator("article[data-idx]").nth(2)
            second.locator("[data-act=skip]").click()
            expect(second).to_be_hidden()
            page.wait_for_timeout(1500)
            page.click("text=What your paper learned")
            expect(page.locator("h1")).to_contain_text("learned")

        scene("sara_learn", sara_learn)

        def sara_archive():
            page.click("text=Archive")
            expect(page.locator("a[href^='/edition/']")).to_have_count(7)
            page.locator("a[href^='/edition/']").last.click()
            expect(page.locator(".badge")).to_contain_text("Backfilled")
            with page.expect_download() as dl:
                page.click("#download")
            pdf = dl.value.path()
            assert Path(pdf).read_bytes()[:4] == b"%PDF"
            import pypdfium2 as pdfium

            img = pdfium.PdfDocument(pdf)[0].render(scale=1.4).to_pil()
            img.save(OUT / "pdf_page.png")
            page.goto((OUT / "pdf_page.png").resolve().as_uri())
            smooth_scroll(700, steps=14, pause=200)

        scene("sara_archive", sara_archive)

        def persona(email, name):
            def go():
                login(email)
                expect(page.locator("h1")).to_contain_text(name)
                page.wait_for_timeout(1500)
                smooth_scroll(1400, steps=18, pause=220)
            return go

        scene("ayesha", persona("ayesha@demo.paper", "Ayesha"))
        scene("bilal", persona("bilal@demo.paper", "Bilal"))

        def onboarding():
            page.goto(f"{BASE}/logout")
            page.goto(f"{BASE}/signup")
            expect(page.locator("#name")).to_be_visible()
            page.goto(f"{BASE}/login")  # show the form flow without spending model quota on a new edition
            page.goto(f"{BASE}/")
            login("bilal@demo.paper")
            page.goto(f"{BASE}/onboarding")
            expect(page.locator("legend")).to_have_count(5)
            for slug in ("cricket", "space", "ai"):
                page.locator(f"input[value={slug}] + span").click()
                page.wait_for_timeout(400)
            page.fill("#free", "Pakistan Super League, Formula 1")

        scene("onboarding", onboarding)

        def architecture():
            page.goto((ROOT / "diagrams" / "architecture.png").resolve().as_uri())
            page.wait_for_timeout(1000)

        scene("architecture", architecture)
        scene("close", lambda: (page.goto(f"{BASE}/logout"), page.goto(BASE), expect(page.locator("h1")).to_contain_text("One paper")))
        video = page.video.path()
        ctx.close()
        b.close()
    (OUT / "scenes.json").write_text(json.dumps({"starts": starts, "qa": qa, "video": str(video)}))
    return starts, qa, video


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def assemble(meta, starts, video):
    # Captions: chunks of <= 7 words from the TTS word timestamps, shifted by the measured scene start.
    lines, n = [], 0
    for name, _ in SCENES:
        ws, off = meta[name]["words"], starts[name]
        for i in range(0, len(ws), 7):
            chunk = ws[i : i + 7]
            n += 1
            lines += [str(n), f"{srt_time(off + chunk[0][0])} --> {srt_time(off + chunk[-1][1])}", " ".join(w for _, _, w in chunk), ""]
    (OUT / "captions.srt").write_text("\n".join(lines), encoding="utf-8")
    inputs, filters = [], []
    for i, (name, _) in enumerate(SCENES):
        inputs += ["-i", str(OUT / f"{name}.mp3")]
        d = int(round(starts[name] * 1000))
        filters.append(f"[{i + 1}:a]adelay={d}|{d}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(SCENES))) + f"amix=inputs={len(SCENES)}:normalize=0[aout]"
    style = "FontName=Segoe UI,FontSize=20,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=28"
    cmd = ["ffmpeg", "-y", "-i", str(video), *inputs, "-filter_complex",
           ";".join(filters) + ";" + mix + f";[0:v]subtitles=captions.srt:force_style='{style}'[vout]",
           "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "morning-paper-demo.mp4"]
    subprocess.run(cmd, check=True, cwd=OUT, capture_output=True)
    return OUT / "morning-paper-demo.mp4"


if __name__ == "__main__":
    meta = narration() if "--reuse-audio" not in sys.argv else json.loads((OUT / "narration.json").read_text())
    print("narration seconds:", round(sum(m["duration"] for m in meta.values()), 1))
    starts, qa, video = record(meta)
    for row in qa:
        print("QA", *row)
    print("video:", assemble(meta, starts, video))
