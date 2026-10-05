from biz_scraper.db import DB
from biz_scraper.models import Listing, parse_money
from biz_scraper.scoring import passes, score
from biz_scraper.sources.generic import HtmlSource
from biz_scraper.sources.places import PlacesSource

HTML = """
<div class="c"><h3><a href="/l/1">Profitable HVAC Co</a></h3><span class="p">$1.2M</span>
<span class="cf">$450,000</span><span class="loc">Austin, TX</span><p class="d">owner retiring</p></div>
<div class="c"><h3><a href="/l/2">Cafe</a></h3><span class="p">Not Disclosed</span></div>
<a class="n" href="/page2">next</a>
"""
CFG = {"name": "t", "type": "html", "start_urls": ["https://x.test/"], "item": "div.c",
       "next_page": "a.n", "fields": {"title": "h3 a", "url": {"selector": "h3 a", "attr": "href"},
       "price": ".p", "cash_flow": ".cf", "location": ".loc", "description": ".d"}}


def test_parse_money():
    assert parse_money("$1,250,000") == 1_250_000
    assert parse_money("$1.2M") == 1_200_000
    assert parse_money("450k") == 450_000
    assert parse_money("Not Disclosed") is None


def test_html_source_parses_and_paginates():
    s = HtmlSource(CFG)
    ls = s.parse_page(HTML, "https://x.test/")
    assert [l.title for l in ls] == ["Profitable HVAC Co", "Cafe"]
    assert ls[0].price == 1_200_000 and ls[0].url == "https://x.test/l/1"
    assert ls[1].price is None
    assert s.next_url(HTML, "https://x.test/") == "https://x.test/page2"


def test_filters_and_score():
    f = {"max_price": 2_000_000, "min_cash_flow": 100_000, "include_keywords": ["retiring"]}
    good = HtmlSource(CFG).parse_page(HTML, "https://x.test/")[0]
    assert passes(good, f) and score(good, f) > 50
    assert not passes(Listing("t", "Big", "u", price=9_000_000), f)
    assert passes(Listing("t", "Unknown", "u"), f)  # missing data never disqualifies


def test_db_dedupes_and_exports(tmp_path):
    db = DB(str(tmp_path / "t.db"))
    l = Listing("t", "A", "https://x/1", price=5)
    assert db.upsert(l, 10) is True
    assert db.upsert(l, 12) is False
    assert db.export_csv(str(tmp_path / "o.csv")) == 1


def test_places_parse_skips_closed():
    s = PlacesSource({"name": "p", "queries": []})
    data = {"places": [
        {"displayName": {"text": "Open Co"}, "websiteUri": "https://o.co", "rating": 4.8,
         "userRatingCount": 100, "businessStatus": "OPERATIONAL"},
        {"displayName": {"text": "Gone"}, "businessStatus": "CLOSED_PERMANENTLY"}]}
    out = s.parse(data)
    assert len(out) == 1 and out[0].extra["rating"] == 4.8
