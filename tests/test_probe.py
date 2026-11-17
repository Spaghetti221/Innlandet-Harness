"""Task 001: the MET probe (harness/probe.py), offline. The network call is replaced."""

import io
import json
import sys
import urllib.error
from email.message import Message
from email.utils import format_datetime
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import probe  # noqa: E402

REAL_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "met_hamar.json"


@pytest.fixture
def paths(tmp_path, monkeypatch):
    """Point the probe's files at tmp_path, starting from a copy of the saved forecast."""
    fixture = tmp_path / "met_hamar.json"
    fixture.write_bytes(REAL_FIXTURE.read_bytes())
    monkeypatch.setattr(probe, "ROOT", tmp_path)
    monkeypatch.setattr(probe, "FIXTURE", fixture)
    monkeypatch.setattr(probe, "OUT", tmp_path / "out" / "probe.json")
    monkeypatch.setattr(probe, "CACHE_META", tmp_path / "out" / "met_cache.json")
    return tmp_path


def _headers(**values) -> Message:
    msg = Message()
    for k, v in values.items():
        msg[k.replace("_", "-")] = v
    return msg


def test_symbol_code_prefers_the_shortest_period():
    assert probe.symbol_code({"next_1_hours": {"summary": {"symbol_code": "rain"}},
                              "next_6_hours": {"summary": {"symbol_code": "cloudy"}}}) == "rain"
    assert probe.symbol_code({"next_12_hours": {"summary": {"symbol_code": "fair_day"}}}) == "fair_day"
    assert probe.symbol_code({}) is None


def test_to_items_from_the_saved_forecast():
    items = probe.to_items(json.loads(REAL_FIXTURE.read_text(encoding="utf-8")))
    assert items and set(items[0]) == {"title", "date", "air_temperature"}
    assert all(isinstance(i["air_temperature"], (int, float)) for i in items)


def test_cache_meta_missing_or_broken(paths):
    assert probe.load_meta() == {}
    probe.CACHE_META.parent.mkdir(parents=True)
    probe.CACHE_META.write_text("{not json", encoding="utf-8")
    assert probe.load_meta() == {}


def test_cache_freshness(paths):
    future = format_datetime(datetime.now(timezone.utc) + timedelta(hours=1))
    past = format_datetime(datetime.now(timezone.utc) - timedelta(hours=1))
    assert probe.cache_is_fresh({"expires": future})
    assert not probe.cache_is_fresh({"expires": past})
    assert not probe.cache_is_fresh({"expires": "not a date"})
    assert not probe.cache_is_fresh({})


def test_fresh_cache_is_not_refetched(paths, monkeypatch):
    probe.CACHE_META.parent.mkdir(parents=True)
    future = format_datetime(datetime.now(timezone.utc) + timedelta(hours=1))
    probe.CACHE_META.write_text(json.dumps({"expires": future}), encoding="utf-8")
    monkeypatch.setattr(probe.urllib.request, "urlopen", lambda *a, **k: pytest.fail("no request"))
    assert probe.fetch()["type"] == "Feature"


def test_new_forecast_is_stored_with_cache_headers(paths, monkeypatch):
    sent = {}

    class Response(io.BytesIO):
        headers = _headers(Expires="Thu, 29 Oct 2026 13:00:00 GMT", Last_Modified="Thu, 29 Oct 2026 12:30:00 GMT")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def urlopen(req, timeout):
        sent["headers"] = dict(req.header_items())
        return Response(b'{"type": "Feature", "new": true}')

    monkeypatch.setattr(probe.urllib.request, "urlopen", urlopen)
    assert probe.fetch() == {"type": "Feature", "new": True}
    assert "User-agent" in sent["headers"]  # MET requires an identifying User-Agent
    meta = json.loads(probe.CACHE_META.read_text(encoding="utf-8"))
    assert meta["last_modified"] == "Thu, 29 Oct 2026 12:30:00 GMT"


def test_not_modified_keeps_the_stored_copy(paths, monkeypatch):
    probe.CACHE_META.parent.mkdir(parents=True)
    probe.CACHE_META.write_text(json.dumps({"last_modified": "Thu, 29 Oct 2026 12:30:00 GMT"}), encoding="utf-8")
    sent = {}

    def urlopen(req, timeout):
        sent["headers"] = dict(req.header_items())
        raise urllib.error.HTTPError(req.full_url, 304, "Not Modified", _headers(), None)

    monkeypatch.setattr(probe.urllib.request, "urlopen", urlopen)
    assert probe.fetch()["type"] == "Feature"
    assert sent["headers"]["If-modified-since"] == "Thu, 29 Oct 2026 12:30:00 GMT"


def test_other_http_errors_are_raised(paths, monkeypatch):
    def urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", _headers(), None)

    monkeypatch.setattr(probe.urllib.request, "urlopen", urlopen)
    with pytest.raises(urllib.error.HTTPError):
        probe.fetch()


def test_main_offline_writes_probe_json(paths, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["probe.py", "--offline"])
    probe.main()
    result = json.loads(probe.OUT.read_text(encoding="utf-8"))
    assert result["source_url"] == probe.SOURCE_URL and result["items"]
