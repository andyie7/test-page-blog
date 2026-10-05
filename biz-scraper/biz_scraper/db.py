from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from .models import Listing

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
  uid TEXT PRIMARY KEY, source TEXT, title TEXT, url TEXT,
  price INTEGER, revenue INTEGER, cash_flow INTEGER,
  location TEXT, description TEXT, extra TEXT, score REAL,
  first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
  last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'new'  -- new | reviewing | contacted | passed
)"""

COLS = ["score", "title", "source", "price", "revenue", "cash_flow", "location",
        "url", "status", "first_seen", "description"]


class DB:
    def __init__(self, path: str):
        self.c = sqlite3.connect(path)
        self.c.row_factory = sqlite3.Row
        self.c.execute(SCHEMA)

    def upsert(self, l: Listing, score: float) -> bool:
        """Returns True if the listing is new."""
        exists = self.c.execute("SELECT 1 FROM listings WHERE uid=?", (l.uid,)).fetchone()
        if exists:
            self.c.execute(
                "UPDATE listings SET price=?, revenue=?, cash_flow=?, score=?, "
                "last_seen=CURRENT_TIMESTAMP WHERE uid=?",
                (l.price, l.revenue, l.cash_flow, score, l.uid))
        else:
            self.c.execute(
                "INSERT INTO listings (uid,source,title,url,price,revenue,cash_flow,"
                "location,description,extra,score) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (l.uid, l.source, l.title, l.url, l.price, l.revenue, l.cash_flow,
                 l.location, l.description, json.dumps(l.extra), score))
        self.c.commit()
        return not exists

    def set_status(self, uid_prefix: str, status: str) -> int:
        cur = self.c.execute("UPDATE listings SET status=? WHERE uid LIKE ?",
                             (status, uid_prefix + "%"))
        self.c.commit()
        return cur.rowcount

    def top(self, limit: int = 25, status: str | None = None):
        q, args = "SELECT * FROM listings", []
        if status:
            q += " WHERE status=?"
            args.append(status)
        return self.c.execute(q + " ORDER BY score DESC LIMIT ?", (*args, limit)).fetchall()

    def export_csv(self, path: str) -> int:
        rows = self.top(limit=10**9)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(COLS)
            w.writerows([[r[c] for c in COLS] for r in rows])
        return len(rows)
