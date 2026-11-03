"""The fetcher honours robots.txt: Disallow and Crawl-delay (offline)."""

from urllib.robotparser import RobotFileParser

import pytest

from harness.hamar_news import fetch
from harness.hamar_news.fetch import LISTING_URL, Fetcher

ROBOTS = ["User-agent: *", "Crawl-delay: 5", "Disallow: /sok/"]


class FakeResponse:
    ok, text, encoding = True, "<html></html>", "utf-8"

    def raise_for_status(self):
        pass


def _fetcher(monkeypatch, sleeps):
    f = Fetcher(delay_seconds=2)
    f._robots = RobotFileParser()
    f._robots.parse(ROBOTS)
    monkeypatch.setattr(f.session, "get", lambda url, timeout: FakeResponse())
    monkeypatch.setattr(fetch.time, "sleep", sleeps.append)
    return f


def test_crawl_delay_overrides_shorter_configured_delay(monkeypatch):
    sleeps: list[float] = []
    f = _fetcher(monkeypatch, sleeps)
    f.get(LISTING_URL)
    f.get(LISTING_URL)
    assert sleeps and sleeps[-1] > 4.9  # waited for the 5 s Crawl-delay, not the configured 2 s


def test_disallowed_path_is_not_fetched(monkeypatch):
    f = _fetcher(monkeypatch, [])
    with pytest.raises(PermissionError):
        f.get("https://www.hamar.kommune.no/sok/?q=test")
