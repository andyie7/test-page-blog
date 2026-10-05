"""Off-market sourcing via the official Google Places API (New): finds
established local businesses by query, e.g. 'HVAC company in Austin TX'.
Requires an API key in the env var named by `api_key_env`."""
from __future__ import annotations

import os
from typing import Iterator

from ..models import Listing

URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ",".join(f"places.{f}" for f in (
    "id", "displayName", "formattedAddress", "websiteUri", "googleMapsUri",
    "nationalPhoneNumber", "rating", "userRatingCount", "businessStatus"))


class PlacesSource:
    def __init__(self, cfg: dict):
        self.name = cfg["name"]
        self.queries = cfg["queries"]
        self.max_per_query = min(cfg.get("max_per_query", 20), 20)
        self.key = os.environ.get(cfg.get("api_key_env", "GOOGLE_PLACES_API_KEY"), "")

    def parse(self, data: dict) -> list[Listing]:
        out = []
        for p in data.get("places", []):
            if p.get("businessStatus", "OPERATIONAL") != "OPERATIONAL":
                continue
            out.append(Listing(
                source=self.name,
                title=p.get("displayName", {}).get("text", ""),
                url=p.get("websiteUri") or p.get("googleMapsUri", ""),
                location=p.get("formattedAddress", ""),
                description="Off-market lead (not listed for sale)",
                extra={"rating": p.get("rating"), "reviews": p.get("userRatingCount"),
                       "phone": p.get("nationalPhoneNumber"), "place_id": p.get("id")},
            ))
        return out

    def fetch(self, http) -> Iterator[Listing]:
        if not self.key:
            print(f"  [skip] {self.name}: set the API key env var")
            return
        for q in self.queries:
            r = http.post(URL, json={"textQuery": q, "pageSize": self.max_per_query},
                          headers={"X-Goog-Api-Key": self.key, "X-Goog-FieldMask": FIELDS})
            if r is not None:
                yield from self.parse(r.json())
