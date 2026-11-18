"""Personal names are removed before the model and rejected after it (offline, synthetic names)."""

import pytest

from harness.hamar_news import names
from harness.hamar_news.check import main as check_main, source_actors
from harness.hamar_news.extract import extract_article
from harness.hamar_news.fetch import LISTING_URL
from harness.hamar_news.names import find_person_names, ner_available, scrub_person_names
from harness.hamar_news.pipeline import run_once
from harness.hamar_news.store import Store
from harness.hamar_news.summarise import MockSummariser, build_hints, build_messages, system_prompt

from test_hamar_news import ARTICLE_URL, FakeFetcher, _pages, fixture

TITLE = "Si din mening om testplan for Eksempelvegen"
CONFIG = {"language": "English", "max_listing_pages": 1, "max_input_tokens": 6000}


def test_finds_and_scrubs_names():
    text = "Kontakt Kari Nordmann eller Ola Bjørn-Nordmann. Planen gjelder Hamar sentrum."
    assert find_person_names(text) == ["Kari Nordmann", "Ola Bjørn-Nordmann"]
    assert scrub_person_names(text) == ("Kontakt [name removed] eller [name removed]. "
                                        "Planen gjelder Hamar sentrum.")


def test_ordinary_text_is_left_alone():
    for text in ("Hamar kommune, Østre torg og Vikingskipet", "Per 1. januar 2027",
                 "Hans bil sto i Ringgata", "The deadline is 30 November 2026."):
        assert find_person_names(text) == []


def test_names_in_body_never_reach_the_model():
    html = fixture("article.html").replace("Kommunen ønsker innspill",
                                           "Saksbehandler Kari Nordmann sier kommunen ønsker innspill")
    article = extract_article(html, ARTICLE_URL)
    assert "Kari Nordmann" not in article.text and "[name removed]" in article.text
    assert not article.names_in_title


def test_article_about_named_people_is_anonymised(tmp_path):
    # The slug stands in for a URL made from a title with a name in it.
    pages = _pages()
    pages[ARTICLE_URL] = pages[ARTICLE_URL].replace(TITLE, "Prisen tildeles Kari Nordmann")
    written = run_once(CONFIG, FakeFetcher(pages), MockSummariser(), Store(tmp_path, mock=True))
    assert len(written) == 1 and written[0].name.split("_", 1)[1].startswith("anon-")
    summary = written[0].read_text(encoding="utf-8")
    assert "# Prisen tildeles [name removed]" in summary
    assert f"<{LISTING_URL}>" in summary
    stored = "".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file())
    names = " ".join(str(p) for p in tmp_path.rglob("*"))
    for leaked in ("Kari", "Nordmann", "eksempelvegen"):  # not in contents, file names or slug
        assert leaked not in stored and leaked not in names
    # Remembered under the hashed slug, so the next run does not summarise it again.
    again = run_once(CONFIG, FakeFetcher(pages), MockSummariser(), Store(tmp_path, mock=True))
    assert again == []
    assert check_main(["--mock", "--out", str(tmp_path)]) == 0


def test_glossary_only_for_english():
    assert "pumping station" in system_prompt("English")
    assert "pumping station" not in system_prompt("German")


def test_names_outside_the_list_are_found_by_context():
    # Run 3 (03.11) leaked a contact person whose first name was not in the list.
    for text, name in [("Spørsmål kan rettes til Xyzzy Qwerty Nordmann, mob. 123", "Xyzzy Qwerty Nordmann"),
                       ("Kontaktperson er Xyzzy Nordmann.", "Xyzzy Nordmann"),
                       ("Xyzzy Nordmann, epost: [email removed]", "Xyzzy Nordmann")]:
        assert find_person_names(text) == [name]
    for text in ("Teknaconsult AS, e-post: x", "Spørsmål kan rettes til saksbehandler på e-post",
                 "Innlandet fylkeskommune kunngjør oppstart"):
        assert find_person_names(text) == []


needs_ner = pytest.mark.skipif(not ner_available("nb"), reason="spaCy model nb_core_news_md not available")


@needs_ner
def test_ner_finds_a_name_with_no_list_match_and_no_cue():
    # Neither first name is in first_names.txt, and no cue phrase or contact detail follows.
    text = "Prosjektet ble presentert av Torvild Bakkerud på møtet i går."
    assert scrub_person_names(text) == "Prosjektet ble presentert av [name removed] på møtet i går."


@needs_ner
def test_ner_leaves_places_and_bodies_alone():
    for text in ("Innlandet fylkeskommune starter arbeidet med Ringgata.",
                 "Planen gjelder Østre torg og Hamar sentrum."):
        assert find_person_names(text) == []


def test_real_run_stops_without_ner(monkeypatch):
    monkeypatch.setattr(names, "ner_available", lambda lang="nb": False)
    with pytest.raises(RuntimeError, match="spacy download"):
        names.require_ner()


def test_hints_follow_the_article_and_name_the_body():
    article_text = "Innlandet fylkeskommune kunngjør oppstart av planarbeid for Ringgata."
    hints = build_hints("English", source_actors(article_text))
    user = build_messages(article_text, "English", hints=hints)[1]["content"]
    assert user.index("</article>") < user.index("Write the summary in English")
    assert "Innlandet fylkeskommune is doing it" in user
    assert len(build_hints("English", [])) == 1  # no body named: only the format reminder


def test_hyphenated_first_name_and_pairs_are_removed():
    # 17.11: the second of two prize winners, with a double first name, was left in the text.
    text = "Prisen går til Kari Nordmann og Ola-Petter Bakkerud ved Eksempelhotellet."
    assert scrub_person_names(text) == "Prisen går til [name removed] og [name removed] ved Eksempelhotellet."
    # Rule 4 needs no list match: a capitalised pair next to a removed name.
    assert scrub_person_names("[name removed] og Xyzzy Qwerty har ordet.") == \
        "[name removed] og [name removed] har ordet."


@needs_ner
def test_ner_skips_single_places_lowercase_words_urls_and_addresses():
    # Labelled as people by the model on 17.11; none is a person.
    for text in ("Trafikksikkerheten på Børstad skal bedres.", "Planen gjelder vann og avløp.",
                 "Utbyggingsavtalen for Jernbanebrygga er godkjent.", "Per 1. januar 2027 gjelder nye satser.",
                 "Se www.hamar.kommune.no/sentrumsplan for kart.", "Møtet er i Eksempelveien 25A."):
        assert find_person_names(text) == [], text


@needs_ner
def test_ner_keeps_a_lone_known_first_name():
    assert find_person_names("Kari og Ola har vist stort samfunnsansvar.") == ["Kari", "Ola"]


def test_ner_span_naming_a_venue_is_not_a_person():
    # 18.11: the English model labelled "<place> Hotell" in a prize notice as a person, and the
    # summary was withheld for a name that was not there. No spaCy needed: the filter alone.
    for text, span in (("Prisen deles ut ved Eksempelstua Hotell og Vandrerhjem.", "Eksempelstua Hotell"),
                       ("The prize is awarded at Eksempelstua Hotel.", "Eksempelstua Hotel"),
                       ("Møtet holdes på Eksempelvik Skole.", "Eksempelvik Skole")):
        start = text.index(span)
        assert not names.accept_ner_span(text, start, start + len(span)), span
    text = "Kontakt Kari Nordmann for spørsmål."
    assert names.accept_ner_span(text, 8, 21)


def test_placeholders_are_static_english_and_old_runs_are_converted(tmp_path):
    from harness.hamar_news.extract import english_placeholders, load_saved_article, scrub_contact_details
    assert scrub_contact_details("Skriv til post@example.no eller ring 12 34 56 78.") == \
        "Skriv til [email removed] eller ring [phone removed]."
    old = "Kontakt [navn fjernet] på [e-post fjernet] eller [telefon fjernet]."
    assert english_placeholders(old) == "Kontakt [name removed] på [email removed] eller [phone removed]."
    article = load_saved_article({"url": "u", "slug": "s", "title": "Pris til [navn fjernet]", "lead": "",
                                  "body": old, "published": "", "modified": "", "expires": ""})
    assert "fjernet" not in article.text
