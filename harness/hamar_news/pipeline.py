"""One polling pass (run_once) and the polling loop (run_forever)."""

import logging
import time
from pathlib import Path

import requests

from .extract import extract_article
from .fetch import discover_articles, slug_of
from .store import Store
from .summarise import truncate

log = logging.getLogger(__name__)


def run_once(config: dict, fetcher, summariser, store: Store) -> list[Path]:
    """Fetch the listing, summarise every article not summarised before. Returns new summary paths."""
    language = config["language"]
    urls = discover_articles(fetcher, config["max_listing_pages"])
    new = [u for u in urls if not store.is_done(slug_of(u))]
    log.info("Found %d article links, %d new", len(urls), len(new))

    written: list[Path] = []
    for url in new:
        try:
            html = fetcher.get(url)
        except Exception as exc:
            log.warning("Could not fetch %s: %s", url, exc)
            continue
        article = extract_article(html, url)
        if article is None:
            log.info("Skipping %s: not a single-article page", url)
            store.mark_skipped(slug_of(url))
            continue
        store.save_html(article.slug, html)
        store.save_text(article)

        text, truncated = truncate(article.text, config["max_input_tokens"])
        try:
            summary = summariser.summarise(text, language)
        except requests.ConnectionError as exc:
            log.error("Model server unreachable (%s); stopping this run, will retry next time", exc)
            break
        except Exception as exc:
            log.error("Summarising %s failed: %s; will retry next run", url, exc)
            continue

        path = store.write_summary(article, summary, language, summariser.name, truncated)
        store.mark_done(article, path, language, summariser.name)
        written.append(path)
        log.info("Wrote %s", path)

    store.write_index()
    return written


def run_forever(config: dict, fetcher, summariser, store: Store, interval_seconds: int) -> None:
    log.info("Polling every %d s (Ctrl+C to stop)", interval_seconds)
    while True:
        try:
            written = run_once(config, fetcher, summariser, store)
            log.info("Run complete: %d new summaries", len(written))
        except Exception:
            log.exception("Run failed; will try again next interval")
        time.sleep(interval_seconds)
