"""CLI: the same pipeline functions the web app calls."""
import argparse
import logging
from datetime import date, datetime

from . import config, db


def _day(s):
    return date.fromisoformat(s) if s else datetime.now(config.PKT).date()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="paper", description="Personal morning paper pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create the database and load topics")
    r = sub.add_parser("run-day", help="shared stages for an edition day: ingest, allowlist, embed")
    r.add_argument("--day")
    b = sub.add_parser("build", help="build one reader's edition for a day")
    b.add_argument("--reader", type=int, required=True)
    b.add_argument("--day")
    b.add_argument("--kind", default="live", choices=["live", "backfilled"])
    d = sub.add_parser("demo", help="seed personas and build 7 days of editions with simulated signals")
    d.add_argument("--days", type=int, default=7)
    sub.add_parser("evaluate", help="persona simulation: learning vs baselines (A10)")
    sub.add_parser("export-demo", help="write demo_data/ for the deployed host")
    a = p.parse_args()

    db.init()
    if a.cmd == "init":
        from . import topics

        topics.load_iptc()
    elif a.cmd == "run-day":
        from . import ingest

        print(ingest.run_day(_day(a.day)))
    elif a.cmd == "build":
        from . import edition

        print(edition.build_edition(a.reader, _day(a.day), a.kind))
    elif a.cmd == "demo":
        from . import simulate

        simulate.demo(a.days)
    elif a.cmd == "evaluate":
        from . import simulate

        print(simulate.evaluate())
    elif a.cmd == "export-demo":
        from . import export

        print(export.export(config.ROOT / "demo_data"))


if __name__ == "__main__":
    main()
