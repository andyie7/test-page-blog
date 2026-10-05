"""Config-driven HTML scraper: works for marketplaces and broker sites once you
give it CSS selectors. No site-specific code needed."""
from __future__ import annotations

from typing import Iterator
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..models import Listing, parse_money


def _extract(node, spec) -> str:
    if not spec:
        return ""
    sel, attr = (spec, None) if isinstance(spec, str) else (spec["selector"], spec.get("attr"))
    el = node.select_one(sel)
    if el is None:
        return ""
    return (el.get(attr, "") if attr else el.get_text(" ", strip=True)).strip()


class HtmlSource:
    def __init__(self, cfg: dict):
        self.name = cfg["name"]
        self.start_urls = cfg["start_urls"]
        self.item = cfg["item"]
        self.fields = cfg["fields"]
        self.next_page = cfg.get("next_page")
        self.max_pages = cfg.get("max_pages", 3)

    def parse_page(self, html: str, page_url: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        out = []
        for node in soup.select(self.item):
            f = {k: _extract(node, v) for k, v in self.fields.items()}
            if not f.get("title"):
                continue
            out.append(Listing(
                source=self.name,
                title=f["title"],
                url=urljoin(page_url, f.get("url", "")),
                price=parse_money(f.get("price")),
                revenue=parse_money(f.get("revenue")),
                cash_flow=parse_money(f.get("cash_flow")),
                location=f.get("location", ""),
                description=f.get("description", ""),
            ))
        return out

    def next_url(self, html: str, page_url: str) -> str | None:
        if not self.next_page:
            return None
        el = BeautifulSoup(html, "html.parser").select_one(self.next_page)
        return urljoin(page_url, el["href"]) if el and el.get("href") else None

    def fetch(self, http) -> Iterator[Listing]:
        for start in self.start_urls:
            url, seen = start, set()
            for _ in range(self.max_pages):
                if not url or url in seen:
                    break
                seen.add(url)
                r = http.get(url)
                if r is None:
                    break
                yield from self.parse_page(r.text, url)
                url = self.next_url(r.text, url)
