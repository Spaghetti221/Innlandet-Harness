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


def test_one_retry_after_a_reset_connection(monkeypatch):
    # 17.11: the site reset one connection and the article was missing from the run.
    import requests
    sleeps: list[float] = []
    f = _fetcher(monkeypatch, sleeps)
    calls = []

    def get(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise requests.ConnectionError("reset by peer")
        return FakeResponse()

    monkeypatch.setattr(f.session, "get", get)
    assert f.get(LISTING_URL) == "<html></html>"
    assert len(calls) == 2 and sleeps and sleeps[-1] >= 5  # waited the Crawl-delay before retrying


def test_robots_txt_is_read_once_and_a_failure_allows_fetching(monkeypatch):
    import requests
    f = Fetcher(delay_seconds=0)
    calls = []

    class Robots:
        ok, text = True, "User-agent: *\nDisallow: /sok/\n"

    def get(url, timeout):
        calls.append(url)
        return Robots()

    monkeypatch.setattr(f.session, "get", get)
    assert f._allowed(LISTING_URL) and not f._allowed("https://www.hamar.kommune.no/sok/?q=x")
    assert calls == ["https://www.hamar.kommune.no/robots.txt"]  # cached after the first read

    g = Fetcher(delay_seconds=0)
    monkeypatch.setattr(g.session, "get", lambda url, timeout: (_ for _ in ()).throw(requests.ConnectionError()))
    assert g._allowed(LISTING_URL)  # robots.txt unreachable: logged, treated as allowed
