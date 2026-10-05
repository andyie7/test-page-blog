# biz-scraper

Finds businesses that may be for sale and ranks them, from three kinds of source:

| Type | Use | Notes |
|------|-----|-------|
| `html` | Marketplaces & broker sites | CSS selectors in config, no code per site |
| `places` | Off-market leads | Official Google Places API, needs `GOOGLE_PLACES_API_KEY` |

Results land in SQLite (deduped by source+URL, first/last seen tracked) and export to CSV.

## Quick start
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml     # edit filters, sources, user_agent
python -m biz_scraper.cli run
python -m biz_scraper.cli list -n 20
python -m biz_scraper.cli mark <uid-prefix> reviewing
python -m biz_scraper.cli export -o exports/listings.csv
pytest
```

## Responsible use
- The scraper honors `robots.txt`, rate-limits per host (default 3s), and identifies itself via `user_agent`.
- Review each site's Terms of Service first. Many marketplaces (e.g. BizBuySell) forbid automated
  scraping. Use their email alerts/RSS/partner APIs there, and use this tool on sites that allow it.
- Off-market leads contain public business info only; no personal data is collected.
  Be mindful of CAN-SPAM/TCPA/local rules when you reach out to owners.

## Scoring
0–100 heuristic: asking-price / cash-flow multiple (lower is better), include-keyword hits,
data completeness, and (off-market) rating + review count. Edit `scoring.py` to match your thesis.
Listings with hidden numbers aren't filtered out, only unscored on those factors.
