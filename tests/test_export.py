"""Offline tests for the JSON export used by the Expo app (harness.hamar_news.export)."""

import json

from harness.hamar_news.export import deadline_from_source, export_runs, kind_of, main, parse_bullets

from test_check import GOOD, FixedSummariser, _run


def test_parse_bullets_keeps_sub_bullets_and_drops_empty_headings():
    md = "* First\n* Residents can:\n  + Read the plan\n  + Comment\n* Deadlines and dates:\n* Last"
    assert parse_bullets(md) == [
        {"text": "First", "children": []},
        {"text": "Residents can:", "children": ["Read the plan", "Comment"]},
        {"text": "Last", "children": []},
    ]


def test_kind_of_title():
    assert kind_of("Oppstart av planarbeid: Si din mening om detaljregulering") == "hearing"
    assert kind_of("Høring: Felles kommunedelplan for vann og avløp") == "hearing"
    assert kind_of("Tilskudd til inkludering av barn og unge 2027") == "grant"
    assert kind_of("Oppstart reguleringsplan fv. 187 Ringgata") == "plan"
    assert kind_of("Ny sentrumsplan er vedtatt") == "decision"
    assert kind_of("Har du en bolig å leie ut?") == "info"


def test_deadline_from_source_handles_compound_words():
    assert deadline_from_source("Uttalefrist er 18. november 2026.", "2026-10-16") == "2026-11-18"
    assert deadline_from_source("høringsfristen er 17. november.", "2026-09-30") == "2026-11-17"
    # A year-less date before publishing belongs to the next year.
    assert deadline_from_source("Frist 10. januar.", "2026-12-01") == "2027-01-10"
    assert deadline_from_source("Vedtatt 28. oktober 2026.", "2026-11-02") is None


def test_export_merges_languages_per_article(tmp_path):
    en, no = tmp_path / "en", tmp_path / "no"
    _run(en, FixedSummariser(GOOD), mock=False)
    _run(no, FixedSummariser(GOOD), mock=False)
    state = no / "state.json"
    data = json.loads(state.read_text(encoding="utf-8"))
    for rec in data["articles"].values():
        rec["language"] = "Norwegian (bokmål)"
    state.write_text(json.dumps(data), encoding="utf-8")

    items = export_runs([en, no], mock=False)
    assert len(items) == 1
    item = items[0]
    assert set(item["summaries"]) == {"en", "no"}
    assert item["url"].startswith("https://www.hamar.kommune.no/lokaldemokrati/")
    assert item["kind"] == "hearing"
    assert len(item["summaries"]["en"]["bullets"]) == 3

    dest = tmp_path / "summaries.json"
    assert main(["--run", str(en), "--run", str(no), "--dest", str(dest)]) == 0
    assert json.loads(dest.read_text(encoding="utf-8")) == items


def test_export_without_run_fails(tmp_path):
    assert main(["--run", str(tmp_path), "--dest", str(tmp_path / "x.json")]) == 1


def test_export_leaves_out_summaries_with_names(tmp_path):
    # Run 3 (03.11): a contact name the scrubbing missed reached one summary.
    _run(tmp_path, FixedSummariser(GOOD + "\n- Questions go to Kari Nordmann."), mock=False)
    items = export_runs([tmp_path], mock=False)
    assert items == []
    assert "Kari" not in json.dumps(items)
