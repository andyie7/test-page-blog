from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field


@dataclass
class Listing:
    source: str
    title: str
    url: str
    price: int | None = None
    revenue: int | None = None
    cash_flow: int | None = None
    location: str = ""
    description: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        """Stable id used for dedupe: source + URL (or title if no URL)."""
        key = f"{self.source}|{self.url or self.title}".lower()
        return hashlib.sha1(key.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)


_MONEY = re.compile(r"([\d][\d,]*\.?\d*)\s*([kKmMbB]?)")
_MULT = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def parse_money(text: str | None) -> int | None:
    """'$1,250,000' -> 1250000, '$1.2M' -> 1200000, 'Not Disclosed' -> None."""
    if not text:
        return None
    m = _MONEY.search(text.replace(" ", " "))
    if not m:
        return None
    try:
        return int(float(m.group(1).replace(",", "")) * _MULT[m.group(2).lower()])
    except ValueError:
        return None
