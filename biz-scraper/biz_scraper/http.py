from __future__ import annotations

import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

DEFAULT_UA = "biz-scraper/0.1 (+personal acquisition research; contact: set USER_AGENT in config)"


class PoliteSession:
    """requests wrapper that honors robots.txt, rate-limits per host, and retries."""

    def __init__(self, user_agent: str = DEFAULT_UA, delay: float = 3.0,
                 respect_robots: bool = True, retries: int = 3, timeout: int = 30):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = user_agent
        self.ua, self.delay, self.respect_robots = user_agent, delay, respect_robots
        self.retries, self.timeout = retries, timeout
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        host = urlparse(url)
        base = f"{host.scheme}://{host.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(f"{base}/robots.txt", timeout=self.timeout)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp = None  # unreachable robots.txt: don't block, rate limit still applies
            self._robots[base] = rp
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(self.ua, url)

    def _wait(self, url: str) -> None:
        host = urlparse(url).netloc
        wait = self._last.get(host, 0) + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def request(self, method: str, url: str, **kw) -> requests.Response | None:
        if not self.allowed(url):
            print(f"  [skip] robots.txt disallows {url}")
            return None
        for attempt in range(self.retries):
            self._wait(url)
            try:
                r = self.s.request(method, url, timeout=self.timeout, **kw)
                if r.status_code in (429, 503):
                    time.sleep(2 ** attempt * 5)
                    continue
                r.raise_for_status()
                return r
            except requests.RequestException as e:
                print(f"  [warn] {url}: {e}")
                time.sleep(2 ** attempt)
        return None

    def get(self, url: str, **kw):
        return self.request("GET", url, **kw)

    def post(self, url: str, **kw):
        return self.request("POST", url, **kw)
