"""Offline tests for harness.hamar_news (no network, no model)."""

import json
from pathlib import Path

import pytest

from harness.hamar_news.config import set_language, load_config
from harness.hamar_news.extract import extract_article
from harness.hamar_news.fetch import (LISTING_URL, article_links, discover_articles,
                                      is_article_url, pagination_links)
from harness.hamar_news.pipeline import run_once
from harness.hamar_news.store import Store
from harness.hamar_news.summarise import MockSummariser, build_messages, truncate

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "hamar_news"
BASE = "https://www.hamar.kommune.no/lokaldemokrati/"
ARTICLE_URL = BASE + "si-din-mening-om-testplan-for-eksempelvegen"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeFetcher:
    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.requested: list[str] = []

    def get(self, url: str) -> str:
        self.requested.append(url)
        if url not in self.pages:
            raise RuntimeError(f"404 {url}")
        return self.pages[url]


@pytest.mark.parametrize("url", [
    ARTICLE_URL,
    BASE + "oppstart-reguleringsplan-fv-187-ringgata-i-hamar",
    BASE + "vil-du-ha-skoyteis-der-du-bor-2/",
])
def test_url_filter_accepts_articles(url):
    assert is_article_url(url)


@pytest.mark.parametrize("url", [
    BASE,
    BASE + "?offset829=1",
    ARTICLE_URL + "#kommentar",
    BASE + "a/b",
    "https://www.hamar.kommune.no/politikk/noe",
    "https://www.example.org/lokaldemokrati/noe",
    "mailto:someone@example.org",
])
def test_url_filter_rejects_non_articles(url):
    assert not is_article_url(url)


def test_listing_links_and_pagination():
    html = fixture("listing.html")
    assert article_links(html) == [
        ARTICLE_URL,
        BASE + "vedtak-om-eksempelpark",
        BASE + "ikke-en-artikkel",
    ]
    assert pagination_links(html) == [BASE + "?offset829=1", BASE + "?offset829=2"]


def test_discover_respects_max_pages():
    fetcher = FakeFetcher({LISTING_URL: fixture("listing.html"),
                           BASE + "?offset829=1": "<html></html>"})
    discover_articles(fetcher, max_pages=2)
    assert fetcher.requested == [LISTING_URL, BASE + "?offset829=1"]


def test_extract_article_text_only():
    article = extract_article(fixture("article.html"), ARTICLE_URL)
    assert article is not None
    assert article.title == "Si din mening om testplan for Eksempelvegen"
    assert article.lead.startswith("Kommunen ønsker innspill")
    assert "planID 0403-9999" in article.body
    assert "- Merk innspillet med saksnummer 26/12345." in article.body
    assert article.published.startswith("2026-10-20")
    assert article.expires.startswith("2026-11-30")
    text = article.text
    for forbidden in ("FOOTER-SHOULD-NOT-APPEAR", "SCRIPT-SHOULD-NOT-APPEAR",
                      "FIXTURE-AUTHOR-NAME", "postmottak@example.org", "12 34 56 78", "<p>"):
        assert forbidden not in text


def test_extract_rejects_non_article():
    assert extract_article(fixture("not_article.html"), BASE + "ikke-en-artikkel") is None


def test_language_persists(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"language": "English", "model": "llama3.2:3b"}), encoding="utf-8")
    set_language("Nynorsk", cfg)
    assert load_config(cfg)["language"] == "Nynorsk"
    assert json.loads(cfg.read_text(encoding="utf-8"))["model"] == "llama3.2:3b"


def test_system_prompt_uses_language_and_wraps_article():
    messages = build_messages("Teksten", "Ukrainian")
    assert "ONLY in Ukrainian" in messages[0]["content"]
    assert messages[1]["content"] == "<article>\nTeksten\n</article>"


def test_truncate():
    assert truncate("kort", 100) == ("kort", False)
    text, cut = truncate("Setning. " * 1000, 100)
    assert cut and len(text) <= 300


def _pages():
    return {
        LISTING_URL: fixture("listing.html"),
        ARTICLE_URL: fixture("article.html"),
        BASE + "ikke-en-artikkel": fixture("not_article.html"),
        # vedtak-om-eksempelpark is missing -> fetch error, must not crash the run
    }


def test_run_once_summarises_each_article_once(tmp_path):
    config = {"language": "German", "max_listing_pages": 1, "max_input_tokens": 6000}
    store = Store(tmp_path, mock=True)

    first = run_once(config, FakeFetcher(_pages()), MockSummariser(), store)
    assert [p.name for p in first] == ["2026-10-20_si-din-mening-om-testplan-for-eksempelvegen.md"]

    md = first[0].read_text(encoding="utf-8")
    assert md.startswith("# Si din mening om testplan for Eksempelvegen")
    assert f"<{ARTICLE_URL}>" in md
    assert "**Summary language:** German" in md
    assert "../../source/si-din-mening-om-testplan-for-eksempelvegen.json" in md
    assert (tmp_path / "source" / "si-din-mening-om-testplan-for-eksempelvegen.json").exists()
    assert not (tmp_path / "html").exists()  # raw HTML is never stored (it holds names)
    assert ARTICLE_URL in (tmp_path / "mock" / "summaries" / "INDEX.md").read_text(encoding="utf-8")

    # A new Store reloads state from disk, like the next scheduled run.
    fetcher = FakeFetcher(_pages())
    second = run_once(config, fetcher, MockSummariser(), Store(tmp_path, mock=True))
    assert second == []
    assert ARTICLE_URL not in fetcher.requested
    assert BASE + "ikke-en-artikkel" not in fetcher.requested  # remembered as skipped

    # Mock state does not stop a real run from summarising.
    assert not Store(tmp_path, mock=False).is_done("si-din-mening-om-testplan-for-eksempelvegen")


def test_failed_summary_is_retried(tmp_path):
    class Broken:
        name = "broken"

        def summarise(self, text, language):
            raise RuntimeError("model error")

    config = {"language": "English", "max_listing_pages": 1, "max_input_tokens": 6000}
    assert run_once(config, FakeFetcher(_pages()), Broken(), Store(tmp_path, mock=False)) == []
    again = run_once(config, FakeFetcher(_pages()), MockSummariser(), Store(tmp_path, mock=False))
    assert len(again) == 1


def test_replay_runs_offline_from_saved_inputs(tmp_path):
    from harness.hamar_news.pipeline import run_replay

    fixtures = FIXTURES / "live-2026-11-05"
    store = Store(tmp_path, mock=True)
    written = run_replay({"language": "English", "max_input_tokens": 6000}, fixtures,
                         MockSummariser(), store)
    assert len(written) == len(list(fixtures.glob("*.json"))) == 10
    # Same input again: nothing new, nothing fetched.
    assert run_replay({"language": "English", "max_input_tokens": 6000}, fixtures,
                      MockSummariser(), Store(tmp_path, mock=True)) == []


def test_saved_inputs_hold_no_personal_data():
    from harness.hamar_news.extract import EMAIL, PHONE
    from harness.hamar_news.names import find_person_names

    for f in (FIXTURES / "live-2026-11-05").glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        text = "\n".join([data["title"], data["lead"], data["body"]])
        assert not find_person_names(text) and not EMAIL.search(text) and not PHONE.search(text), f.name
