"""Offline tests for the output checker (harness.hamar_news.check)."""

from pathlib import Path

from harness.hamar_news.check import check_run, find_dates, main
from harness.hamar_news.pipeline import run_once
from harness.hamar_news.store import Store
from harness.hamar_news.summarise import MockSummariser

from test_hamar_news import ARTICLE_URL, FakeFetcher, _pages

CONFIG = {"language": "English", "max_listing_pages": 1, "max_input_tokens": 6000}
SUMMARY = "2026-10-20_si-din-mening-om-testplan-for-eksempelvegen.md"


class FixedSummariser:
    """Stands in for the model with a summary we choose."""

    def __init__(self, text: str, name: str = "llama3.2:3b"):
        self.text, self.name = text, name

    def summarise(self, text: str, language: str, previous=None, problems=None) -> str:
        return self.text


def _run(tmp_path: Path, summariser, mock: bool) -> Path:
    run_once(CONFIG, FakeFetcher(_pages()), summariser, Store(tmp_path, mock=mock))
    return tmp_path


def _failures(tmp_path: Path, mock: bool = False) -> list[str]:
    results, problems = check_run(tmp_path, mock)
    return [f for r in results for f in r.failures] + problems


GOOD = ("- The municipality asks for comments on a test plan for Eksempelvegen.\n"
        "- It concerns planID 0403-9999.\n"
        "- Comments are due 30. november 2026.")


def test_find_dates_handles_norwegian_and_english():
    assert find_dates("frist 30. november 2026") == {(2026, 11, 30)}
    assert find_dates("by November 30, 2026") == {(2026, 11, 30)}
    assert find_dates("innen 30.11.2026 eller 2026-11-30") == {(2026, 11, 30)}


def test_mock_run_passes(tmp_path):
    _run(tmp_path, MockSummariser(), mock=True)
    assert _failures(tmp_path, mock=True) == []
    assert main(["--mock", "--out", str(tmp_path)]) == 0


def test_good_real_summary_passes(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD), mock=False)
    assert _failures(tmp_path) == []


def test_invented_date_fails(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD.replace("30. november", "15. desember")), mock=False)
    assert any(f.startswith("no_invented_dates") for f in _failures(tmp_path))
    assert main(["--out", str(tmp_path)]) == 1


def test_contact_details_fail(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD + "\n- Mail postmottak@example.org"), mock=False)
    assert any(f.startswith("no_contact_details") for f in _failures(tmp_path))


def test_too_few_bullets_fail(tmp_path):
    _run(tmp_path, FixedSummariser("- Only one bullet."), mock=False)
    assert any(f.startswith("summary_shape") for f in _failures(tmp_path))


def test_tampered_link_and_orphan_fail(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD), mock=False)
    path = tmp_path / "summaries" / SUMMARY
    path.write_text(path.read_text(encoding="utf-8").replace(ARTICLE_URL, "https://example.org/x"),
                    encoding="utf-8")
    (tmp_path / "summaries" / "2026-01-01_orphan.md").write_text("# Orphan\n", encoding="utf-8")
    failures = _failures(tmp_path)
    assert any(f.startswith("source_link") for f in failures)
    assert any("orphan" in f for f in failures)


def test_empty_run_fails(tmp_path):
    assert main(["--out", str(tmp_path)]) == 1


def test_sub_points_fail(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD + "\n  - an indented sub-point"), mock=False)
    assert any(f.startswith("summary_shape") for f in _failures(tmp_path))


def test_repeated_bullet_fails(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD + "\n- It concerns planID 0403-9999."), mock=False)
    assert any("more than once" in f for f in _failures(tmp_path))


def test_person_name_in_summary_fails_without_leaking_it(tmp_path):
    _run(tmp_path, FixedSummariser(GOOD + "\n- Contact person is Kari Nordmann."), mock=False)
    failures = _failures(tmp_path)
    assert any(f.startswith("no_personal_names") for f in failures)
    assert not any("Kari" in f for f in failures)


def test_missing_deadline_fails(tmp_path):
    no_deadline = "\n".join(GOOD.splitlines()[:2] + ["- Comments can be sent by post."])
    _run(tmp_path, FixedSummariser(no_deadline), mock=False)
    failures = _failures(tmp_path)
    assert any(f.startswith("deadline_kept") and "30.11" in f for f in failures)


class SecondTimeRight:
    """Breaks the rules first; fixes it once it is told what was wrong."""

    name = "llama3.2:3b"

    def __init__(self):
        self.calls: list[list[str] | None] = []

    def summarise(self, text, language, previous=None, problems=None):
        self.calls.append(problems)
        return GOOD if problems else GOOD + "\n  - an indented sub-point"


def test_retry_with_feedback_repairs_summary(tmp_path):
    model = SecondTimeRight()
    _run(tmp_path, model, mock=False)
    assert len(model.calls) == 2 and model.calls[0] is None
    assert any(p.startswith("summary_shape") for p in model.calls[1])  # the model was told why
    md = (tmp_path / "summaries" / SUMMARY).read_text(encoding="utf-8")
    assert "**Attempts:** 2" in md and "still failing" not in md
    assert _failures(tmp_path) == []


def test_retries_stop_and_failure_is_flagged(tmp_path):
    model = FixedSummariser("- Only one bullet.")
    _run(tmp_path, model, mock=False)
    md = (tmp_path / "summaries" / SUMMARY).read_text(encoding="utf-8")
    assert "**Attempts:** 3" in md and "still failing after 3" in md
    assert any(f.startswith("summary_shape") for f in _failures(tmp_path))
