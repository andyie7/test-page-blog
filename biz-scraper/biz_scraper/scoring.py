from __future__ import annotations

from .models import Listing


def passes(l: Listing, f: dict) -> bool:
    """Hard filters. Missing numbers never disqualify (many listings hide them)."""
    for val, lo, hi in ((l.price, f.get("min_price"), f.get("max_price")),
                        (l.revenue, f.get("min_revenue"), None),
                        (l.cash_flow, f.get("min_cash_flow"), None)):
        if val is None:
            continue
        if lo is not None and val < lo or hi is not None and val > hi:
            return False
    text = f"{l.title} {l.description}".lower()
    if any(k.lower() in text for k in f.get("exclude_keywords", [])):
        return False
    locs = f.get("locations", [])
    return not locs or not l.location or any(x.lower() in l.location.lower() for x in locs)


def score(l: Listing, f: dict) -> float:
    """0-100 heuristic: price/cash-flow multiple, keyword hits, data completeness."""
    s = 0.0
    if l.price and l.cash_flow and l.cash_flow > 0:
        mult = l.price / l.cash_flow  # SDE multiple; small businesses often trade ~2-4x
        s += 50 if mult <= 3 else 35 if mult <= 4 else 20 if mult <= 5 else 5
    text = f"{l.title} {l.description}".lower()
    hits = sum(k.lower() in text for k in f.get("include_keywords", []))
    s += min(hits * 10, 30)
    s += 5 * sum(x is not None for x in (l.price, l.revenue, l.cash_flow))
    rating, reviews = l.extra.get("rating"), l.extra.get("reviews")
    if rating and reviews and rating >= 4.3 and reviews >= 25:
        s += 10  # off-market: well-loved, established
    return round(min(s, 100), 1)
