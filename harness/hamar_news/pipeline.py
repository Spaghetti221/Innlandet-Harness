"""One polling pass (run_once), an offline pass over saved inputs (run_replay), and the polling
loop (run_forever)."""

import json
import logging
import time
from pathlib import Path

import requests

from .check import validate_summary
from .extract import Article, extract_article
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
        if article.names_in_title:
            # About named people (e.g. a prize to individuals): nothing is stored, not even the URL.
            log.info("Rejected article %s: its title names people", store.digest(article.slug))
            store.mark_rejected(article.slug)
            continue
        try:
            path = process_article(article, config, summariser, store)
        except requests.ConnectionError as exc:
            log.error("Model server unreachable (%s); stopping this run, will retry next time", exc)
            break
        if path is not None:
            written.append(path)

    store.write_index()
    return written


def process_article(article: Article, config: dict, summariser, store: Store) -> Path | None:
    """Store the cleaned article, summarise it with checks and retries, and write the summary.
    Returns the summary path, or None if summarising failed (it is retried on the next run).
    A ConnectionError from the model server is passed on so the caller can stop the run."""
    language = config["language"]
    store.save_source(article)
    store.save_text(article)
    text, truncated = truncate(article.text, config["max_input_tokens"])
    try:
        summary, attempts, problems = summarise_checked(summariser, article, text, language,
                                                        config.get("max_attempts", 3), store)
    except requests.ConnectionError:
        raise
    except Exception as exc:
        log.error("Summarising %s failed: %s; will retry next run", article.url, exc)
        return None
    path = store.write_summary(article, summary, language, summariser.name, truncated,
                               attempts=attempts, problems=problems)
    store.mark_done(article, path, language, summariser.name, attempts, problems)
    log.info("Wrote %s", path)
    return path


def run_replay(config: dict, source_dir: Path, summariser, store: Store) -> list[Path]:
    """Summarise saved, cleaned inputs (fixtures) instead of fetching the site: no network, and
    the same input every time, so runs and evaluations can be repeated after articles expire."""
    files = sorted(Path(source_dir).glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no saved inputs (*.json) in {source_dir}")
    written: list[Path] = []
    for f in files:
        article = Article(**json.loads(f.read_text(encoding="utf-8")))
        if store.is_done(article.slug) or article.names_in_title:
            continue
        try:
            path = process_article(article, config, summariser, store)
        except requests.ConnectionError as exc:
            log.error("Model server unreachable (%s); stopping the replay", exc)
            break
        if path is not None:
            written.append(path)
    store.write_index()
    log.info("Replayed %d saved inputs from %s", len(files), source_dir)
    return written


def summarise_checked(summariser, article, text: str, language: str,
                      max_attempts: int, store: Store | None = None) -> tuple[str, int, list[str]]:
    """Summarise, check the result with code, and if it breaks a rule, give the problems back
    to the model and let it try again. Returns the last summary, the number of attempts and
    the problems that remain (empty if the summary passed)."""
    is_mock = summariser.name == "mock"
    previous: str | None = None
    problems: list[str] = []
    for attempt in range(1, max(1, max_attempts) + 1):
        if previous is None:
            summary = summariser.summarise(text, language)
        else:
            summary = summariser.summarise(text, language, previous=previous, problems=problems)
        problems = validate_summary(summary, article, is_mock, language)
        if store is not None:
            store.save_attempt(article.slug, attempt, summary, problems)
        if not problems:
            return summary, attempt, []
        log.info("Attempt %d for %s failed the check: %s", attempt, article.slug, "; ".join(problems))
        previous = summary
    return summary, attempt, problems


def run_forever(config: dict, fetcher, summariser, store: Store, interval_seconds: int) -> None:
    log.info("Polling every %d s (Ctrl+C to stop)", interval_seconds)
    while True:
        try:
            written = run_once(config, fetcher, summariser, store)
            log.info("Run complete: %d new summaries", len(written))
        except Exception:
            log.exception("Run failed; will try again next interval")
        time.sleep(interval_seconds)
