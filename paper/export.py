"""Export a self-contained demo dataset for the deployed host (ephemeral disk): personas, their editions and PDFs,
and the latest day's items so new sign-ups can get an edition. Drops sessions and non-persona accounts."""
import shutil
import sqlite3
from pathlib import Path

from . import config


def export(dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "editions").mkdir(exist_ok=True)
    out = dest / "paper.db"
    out.unlink(missing_ok=True)
    work = dest / "work.db"
    work.unlink(missing_ok=True)
    src = sqlite3.connect(config.DB_PATH)
    dst = sqlite3.connect(work)
    src.backup(dst)
    src.close()
    latest = dst.execute("SELECT MAX(day) FROM items").fetchone()[0]
    dst.execute("DELETE FROM sessions")
    keep = "SELECT id FROM readers WHERE persona IS NOT NULL"
    for t, col in (("events", "reader_id"), ("reader_topics", "reader_id"), ("editions", "reader_id")):
        dst.execute(f"DELETE FROM {t} WHERE {col} NOT IN ({keep})")
    dst.execute("DELETE FROM topics WHERE kind='custom' AND owner NOT IN (" + keep + ")")
    dst.execute("DELETE FROM readers WHERE persona IS NULL")
    dst.execute("DELETE FROM items WHERE day <> ?", (latest,))
    dst.execute("UPDATE items SET feed_body=NULL, vec=NULL")  # vectors are recomputed at startup by the baked-in local model
    dst.commit()
    dst.execute("VACUUM INTO ?", (str(out),))  # fresh compact file; in-place VACUUM did not truncate on Windows
    pdfs = [r[0] for r in dst.execute("SELECT pdf_path FROM editions WHERE pdf_path IS NOT NULL")]
    dst.close()
    work.unlink()
    for p in pdfs:
        shutil.copy2(config.EDITIONS / p, dest / "editions" / p)
    return {"db_mb": round(out.stat().st_size / 1e6, 1), "pdfs": len(pdfs), "latest_day": latest}
