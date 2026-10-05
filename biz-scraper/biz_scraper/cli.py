from __future__ import annotations

import argparse
import sys

import yaml

from .db import DB
from .http import DEFAULT_UA, PoliteSession
from .scoring import passes, score
from .sources import build_source


def cmd_run(cfg: dict, db: DB, only: str | None) -> None:
    http = PoliteSession(cfg.get("user_agent", DEFAULT_UA), cfg.get("delay_seconds", 3.0),
                         cfg.get("respect_robots", True))
    filters = cfg.get("filters", {})
    for sc in cfg["sources"]:
        if only and sc["name"] != only:
            continue
        print(f"Source: {sc['name']}")
        seen = new = 0
        for l in build_source(sc).fetch(http):
            seen += 1
            if passes(l, filters):
                new += db.upsert(l, score(l, filters))
        print(f"  {seen} scraped, {new} new after filters")


def cmd_list(db: DB, limit: int, status: str | None) -> None:
    for r in db.top(limit, status):
        price = f"${r['price']:,}" if r["price"] else "n/a"
        print(f"{r['uid'][:8]}  {r['score']:>5}  {price:>12}  {r['title'][:50]:<50}  {r['url']}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="biz-scraper")
    p.add_argument("-c", "--config", default="config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--source")
    l = sub.add_parser("list"); l.add_argument("-n", type=int, default=25); l.add_argument("--status")
    e = sub.add_parser("export"); e.add_argument("-o", default="exports/listings.csv")
    m = sub.add_parser("mark"); m.add_argument("uid"); m.add_argument("status",
        choices=["new", "reviewing", "contacted", "passed"])
    a = p.parse_args(argv)

    try:
        cfg = yaml.safe_load(open(a.config))
    except FileNotFoundError:
        sys.exit(f"No {a.config}: copy config.example.yaml to config.yaml first.")
    db = DB(cfg.get("database", "listings.db"))
    if a.cmd == "run":
        cmd_run(cfg, db, a.source)
    elif a.cmd == "list":
        cmd_list(db, a.n, a.status)
    elif a.cmd == "export":
        print(f"Exported {db.export_csv(a.o)} rows to {a.o}")
    elif a.cmd == "mark":
        print(f"Updated {db.set_status(a.uid, a.status)} listing(s)")


if __name__ == "__main__":
    main()
