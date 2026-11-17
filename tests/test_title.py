"""Task 009: the title is translated in its own call, checked, and retried (offline)."""

import json

import pytest
import requests

from harness.hamar_news.check import clean_title, main as check_main, title_problems
from harness.hamar_news.export import export_runs
from harness.hamar_news.extract import Article
from harness.hamar_news.pipeline import run_once, translate_title_checked
from harness.hamar_news.store import Store
from harness.hamar_news.summarise import MockSummariser, needs_title_translation, title_messages

from test_hamar_news import FakeFetcher, _pages

TITLE = "Si din mening om reguleringsplan for Eksempelvegen"
ARTICLE = Article("u", "eksempel", TITLE, "", "Frist for innspill er 30. november 2026.", "2026-10-20", "", "")
CONFIG = {"language": "English", "max_listing_pages": 1, "max_input_tokens": 6000}


class Translator:
    """Answers with the given titles in turn and records what it was told."""

    name = "llama3.2:3b"

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def translate_title(self, title, language, previous=None, problems=None):
        self.calls.append(problems)
        return self.answers.pop(0)


def test_only_non_norwegian_languages_get_a_translated_title():
    assert needs_title_translation("English") and needs_title_translation("German")
    for lang in ("Norwegian", "Norsk", "Bokmål", "Nynorsk"):
        assert not needs_title_translation(lang)


def test_title_messages_glossary_and_retry():
    system, user = title_messages(TITLE, "English")
    assert "into English" in system["content"] and "zoning plan" in system["content"]  # glossary
    assert user["content"] == f"<title>{TITLE}</title>"
    assert "zoning plan" not in title_messages(TITLE, "German")[0]["content"]
    retry = title_messages(TITLE, "English", previous="Old", problems=["title_shape: x"])
    assert [m["role"] for m in retry] == ["system", "user", "assistant", "user"]
    assert "title_shape: x" in retry[-1]["content"]


def test_clean_title_removes_wrapping_only():
    for raw in ('"Have your say on the zoning plan"', "# Have your say on the zoning plan",
                "Title: Have your say on the zoning plan", "- Have your say on the zoning plan",
                "«Have your say on the zoning plan»"):
        assert clean_title(raw) == "Have your say on the zoning plan"


def test_a_good_title_passes():
    assert title_problems("Have your say on the zoning plan for Eksempelvegen", ARTICLE, "English", False) == []


@pytest.mark.parametrize("title, check", [
    (TITLE, "title_language"),                                          # not translated
    ("Have your say\non the zoning plan", "title_shape"),               # two lines
    ("", "title_shape"),
    ("Have your say on the zoning plan " + "for the area " * 20, "title_shape"),  # far too long
    ("Have your say on the zoning plan by 30 November 2026", "no_invented_dates"),  # date only in body
    ("Have your say on the [date] zoning plan", "invented_placeholder"),
    ("Have your say on the reguleringsplan for Eksempelvegen", "untranslated"),
    ("Kari Nordmann wants comments on the zoning plan", "no_personal_names"),
])
def test_bad_titles_are_caught(title, check):
    assert any(p.startswith(check) for p in title_problems(title, ARTICLE, "English", False))


def test_title_is_retried_with_the_problems(tmp_path):
    model = Translator(TITLE, "Have your say on the zoning plan for Eksempelvegen")
    store = Store(tmp_path, mock=False)
    assert translate_title_checked(model, ARTICLE, "English", 3, store) == \
        "Have your say on the zoning plan for Eksempelvegen"
    assert model.calls[0] is None and "title_language" in model.calls[1][0]
    attempts = sorted(p.name for p in (tmp_path / "attempts" / "eksempel").iterdir())
    assert attempts == ["title-attempt-1.md", "title-attempt-2.md"]


def test_norwegian_title_is_kept_when_no_attempt_passes():
    model = Translator(TITLE, TITLE, TITLE)
    assert translate_title_checked(model, ARTICLE, "English", 3) is None
    assert len(model.calls) == 3


def test_no_call_for_norwegian_or_a_summariser_without_titles():
    model = Translator()
    assert translate_title_checked(model, ARTICLE, "Norwegian", 3) is None and model.calls == []

    class SummaryOnly:
        name = "llama3.2:3b"
    assert translate_title_checked(SummaryOnly(), ARTICLE, "English", 3) is None


def test_errors_keep_the_norwegian_title_but_a_lost_server_stops_the_run():
    class Broken:
        name = "llama3.2:3b"

        def __init__(self, exc):
            self.exc = exc

        def translate_title(self, *args, **kwargs):
            raise self.exc

    assert translate_title_checked(Broken(RuntimeError("bad json")), ARTICLE, "English", 3) is None
    with pytest.raises(requests.ConnectionError):
        translate_title_checked(Broken(requests.ConnectionError()), ARTICLE, "English", 3)


def test_translated_title_heads_the_summary_and_reaches_the_app(tmp_path):
    [path] = run_once(CONFIG, FakeFetcher(_pages()), MockSummariser(), Store(tmp_path, mock=True))
    md = path.read_text(encoding="utf-8")
    original = "Si din mening om testplan for Eksempelvegen"
    assert md.startswith(f"# {original} (English, mock)\n")
    assert f"- **Original title:** {original}\n" in md
    assert path.name == "2026-10-20_si-din-mening-om-testplan-for-eksempelvegen.md"  # slug kept
    state = json.loads((tmp_path / "mock" / "state.json").read_text(encoding="utf-8"))
    assert state["articles"]["si-din-mening-om-testplan-for-eksempelvegen"]["title_translated"].endswith("(English, mock)")
    assert check_main(["--mock", "--out", str(tmp_path)]) == 0

    [item] = export_runs([tmp_path], mock=True)
    assert item["title"] == original and item["kind"] == "hearing"  # Norwegian decides the kind
    assert item["summaries"]["en"]["title"] == f"{original} (English, mock)"


def test_check_catches_an_original_title_that_does_not_match(tmp_path):
    [path] = run_once(CONFIG, FakeFetcher(_pages()), MockSummariser(), Store(tmp_path, mock=True))
    md = path.read_text(encoding="utf-8").replace("- **Original title:** Si din", "- **Original title:** Si ikke")
    path.write_text(md, encoding="utf-8")
    assert check_main(["--mock", "--out", str(tmp_path)]) == 1
