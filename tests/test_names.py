"""Personal names are removed before the model and rejected after it (offline, synthetic names)."""

import json

from harness.hamar_news.extract import extract_article
from harness.hamar_news.names import find_person_names, scrub_person_names
from harness.hamar_news.pipeline import run_once
from harness.hamar_news.store import Store
from harness.hamar_news.summarise import MockSummariser, system_prompt

from test_hamar_news import ARTICLE_URL, FakeFetcher, _pages, fixture

TITLE = "Si din mening om testplan for Eksempelvegen"
CONFIG = {"language": "English", "max_listing_pages": 1, "max_input_tokens": 6000}


def test_finds_and_scrubs_names():
    text = "Kontakt Kari Nordmann eller Ola Bjørn-Nordmann. Planen gjelder Hamar sentrum."
    assert find_person_names(text) == ["Kari Nordmann", "Ola Bjørn-Nordmann"]
    assert scrub_person_names(text) == ("Kontakt [navn fjernet] eller [navn fjernet]. "
                                        "Planen gjelder Hamar sentrum.")


def test_ordinary_text_is_left_alone():
    for text in ("Hamar kommune, Østre torg og Vikingskipet", "Per 1. januar 2027",
                 "Hans bil sto i Ringgata", "The deadline is 30 November 2026."):
        assert find_person_names(text) == []


def test_names_in_body_never_reach_the_model():
    html = fixture("article.html").replace("Kommunen ønsker innspill",
                                           "Saksbehandler Kari Nordmann sier kommunen ønsker innspill")
    article = extract_article(html, ARTICLE_URL)
    assert "Kari Nordmann" not in article.text and "[navn fjernet]" in article.text
    assert not article.names_in_title


def test_article_about_named_people_is_rejected_and_not_stored(tmp_path):
    pages = _pages()
    pages[ARTICLE_URL] = pages[ARTICLE_URL].replace(TITLE, "Prisen tildeles Kari Nordmann")
    store = Store(tmp_path, mock=True)
    assert run_once(CONFIG, FakeFetcher(pages), MockSummariser(), store) == []
    stored = "".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file())
    assert "Kari" not in stored and "eksempelvegen" not in stored  # no name, not even the slug
    # Remembered by hash, so the next run does not fetch it again.
    fetcher = FakeFetcher(pages)
    run_once(CONFIG, fetcher, MockSummariser(), Store(tmp_path, mock=True))
    assert ARTICLE_URL not in fetcher.requested
    assert json.loads((tmp_path / "mock" / "state.json").read_text())["rejected"]


def test_glossary_only_for_english():
    assert "pumping station" in system_prompt("English")
    assert "pumping station" not in system_prompt("German")


def test_names_outside_the_list_are_found_by_context():
    # Run 3 (03.11) leaked a contact person whose first name was not in the list.
    for text, name in [("Spørsmål kan rettes til Xyzzy Qwerty Nordmann, mob. 123", "Xyzzy Qwerty Nordmann"),
                       ("Kontaktperson er Xyzzy Nordmann.", "Xyzzy Nordmann"),
                       ("Xyzzy Nordmann, epost: [e-post fjernet]", "Xyzzy Nordmann")]:
        assert find_person_names(text) == [name]
    for text in ("Teknaconsult AS, e-post: x", "Spørsmål kan rettes til saksbehandler på e-post",
                 "Innlandet fylkeskommune kunngjør oppstart"):
        assert find_person_names(text) == []
