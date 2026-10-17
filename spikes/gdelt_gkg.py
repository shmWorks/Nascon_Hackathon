"""Spike: GDELT GKG 15-minute raw file (no API throttle) for a past day: URLs, titles, images, themes, video."""
import csv
import io
import re
import sys
import time
import zipfile
from collections import Counter

import httpx

csv.field_size_limit(10**8)
stamp = sys.argv[1] if len(sys.argv) > 1 else "20261012060000"
t0 = time.perf_counter()
r = httpx.get(f"https://data.gdeltproject.org/gdeltv2/{stamp}.gkg.csv.zip", timeout=60)
print("status", r.status_code, "bytes", len(r.content), f"{time.perf_counter() - t0:.1f}s")
raw = zipfile.ZipFile(io.BytesIO(r.content)).read(zipfile.ZipFile(io.BytesIO(r.content)).namelist()[0])
rows = list(csv.reader(io.StringIO(raw.decode("utf-8", "replace")), delimiter="\t"))
# GKG 2.1 columns: 0 GKGRECORDID, 1 DATE, 3 SourceCommonName, 4 DocumentIdentifier, 8 V2Themes(7 Themes),
# 18 SharingImage, 19 RelatedImages, 20 SocialImageEmbeds, 21 SocialVideoEmbeds, 26 Extras
title = lambda x: (re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", x[26]) or [None, ""])[1] if len(x) > 26 else ""
n = len(rows)
print("rows", n, "cols", Counter(len(x) for x in rows).most_common(2))
print("with title", sum(1 for x in rows if title(x)), "| with SharingImage", sum(1 for x in rows if len(x) > 18 and x[18]), "| with video embeds", sum(1 for x in rows if len(x) > 21 and x[21]))
themes = Counter(t.split(",")[0] for x in rows if len(x) > 8 for t in x[8].split(";") if t)
print("top themes", [k for k, _ in themes.most_common(12)])
for x in rows[:4]:
    print(" ", x[1], x[3], "|", title(x)[:70], "| img" if x[18] else "")
eng = [x for x in rows if re.search(r"\b(cricket|wicket)\b", title(x), re.I)]
print("cricket-titled rows in this 15-min file:", len(eng))
