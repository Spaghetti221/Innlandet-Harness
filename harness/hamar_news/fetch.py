"""Polite HTTP fetching and discovery of article URLs on the listing pages."""

import logging
import re
import time
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HOST = "www.hamar.kommune.no"
LISTING_URL = f"https://{HOST}/lokaldemokrati/"
USER_AGENT = "InnlandetHarness/0.1 (student project; polls a few pages every few hours)"

# Articles live directly under /lokaldemokrati/ as a single slug segment.
ARTICLE_PATH = re.compile(r"^/lokaldemokrati/[a-z0-9]+(?:-[a-z0-9]+)*/?$")
# Pagination links look like ?offset829=2 (the number after "offset" is a page-module id).
PAGINATION_PARAM = re.compile(r"^offset\d+$")


def is_article_url(url: str) -> bool:
    parts = urlsplit(url)
    return (
        parts.scheme in ("http", "https")
        and parts.netloc == HOST
        and not parts.query
        and not parts.fragment
        and bool(ARTICLE_PATH.match(parts.path))
    )


def normalise_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(("https", parts.netloc, parts.path.rstrip("/"), "", ""))


def slug_of(url: str) -> str:
    return urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]


def article_links(html: str, base_url: str = LISTING_URL) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: dict[str, None] = {}
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        if is_article_url(url):
            links[normalise_url(url)] = None
    return list(links)


def pagination_links(html: str, base_url: str = LISTING_URL) -> list[str]:
    """Return listing pages 2..n in page order, as found on the first listing page."""
    soup = BeautifulSoup(html, "html.parser")
    pages: dict[int, str] = {}
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        parts = urlsplit(url)
        if parts.netloc != HOST or parts.path != "/lokaldemokrati/":
            continue
        query = parse_qsl(parts.query)
        if len(query) == 1 and PAGINATION_PARAM.match(query[0][0]) and query[0][1].isdigit():
            pages[int(query[0][1])] = url
    return [pages[n] for n in sorted(pages) if n > 0]


class Fetcher:
    def __init__(self, delay_seconds: float = 2.0, timeout: float = 30.0):
        self.delay = delay_seconds
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self._last_request = 0.0
        self._robots: RobotFileParser | None = None

    def _allowed(self, url: str) -> bool:
        if self._robots is None:
            self._robots = RobotFileParser()
            try:
                resp = self.session.get(f"https://{HOST}/robots.txt", timeout=self.timeout)
                self._robots.parse(resp.text.splitlines() if resp.ok else [])
            except requests.RequestException:
                log.warning("Could not read robots.txt; assuming allowed")
                self._robots.parse([])
        return self._robots.can_fetch(USER_AGENT, url)

    def get(self, url: str) -> str:
        if not self._allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        # Honour the site's Crawl-delay (5 s on hamar.kommune.no) if it is longer than ours.
        delay = max(self.delay, self._robots.crawl_delay(USER_AGENT) or 0)
        wait = delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            resp = self.session.get(url, timeout=self.timeout)
        finally:
            self._last_request = time.monotonic()
        resp.raise_for_status()
        resp.encoding = resp.encoding or "utf-8"
        return resp.text


def discover_articles(fetcher, max_pages: int) -> list[str]:
    """Collect article URLs from the listing and up to max_pages-1 further pages."""
    first = fetcher.get(LISTING_URL)
    urls = dict.fromkeys(article_links(first))
    for page_url in pagination_links(first)[: max(0, max_pages - 1)]:
        try:
            urls.update(dict.fromkeys(article_links(fetcher.get(page_url))))
        except Exception as exc:  # one bad page should not stop the run
            log.warning("Skipping listing page %s: %s", page_url, exc)
    return list(urls)
