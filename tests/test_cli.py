"""The command line, config, the polling loop, the Ollama client and pipeline error paths (offline)."""

import json
from pathlib import Path

import pytest
import requests

from harness.hamar_news import __main__ as cli
from harness.hamar_news import names, pipeline, summarise
from harness.hamar_news.config import interval_for, load_config, set_language
from harness.hamar_news.pipeline import run_forever, run_once, run_replay
from harness.hamar_news.store import Store
from harness.hamar_news.summarise import MockSummariser, OllamaSummariser, truncate

from test_hamar_news import FakeFetcher, _pages

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "hamar_news" / "live-2026-11-05"
CONFIG = {"language": "English", "max_listing_pages": 1, "max_input_tokens": 6000}


# --- config ------------------------------------------------------------------------------------

def test_config_defaults_and_language_is_saved(tmp_path):
    path = tmp_path / "config.json"
    assert load_config(path)["language"] == "English"  # no file: defaults
    set_language("  Norwegian ", path)
    assert json.loads(path.read_text(encoding="utf-8"))["language"] == "Norwegian"
    assert load_config(path)["language"] == "Norwegian"
    with pytest.raises(ValueError):
        set_language("   ", path)


def test_interval_for_known_and_unknown_profile(tmp_path):
    config = load_config(tmp_path / "none.json")
    assert interval_for(config, "test") == 30
    assert interval_for(config, "prod") == 6 * 60 * 60
    with pytest.raises(ValueError, match="Unknown profile"):
        interval_for(config, "weekly")


# --- command line ------------------------------------------------------------------------------

def test_parse_args_defaults():
    args = cli.parse_args([])
    assert (args.once, args.mock, args.replay, args.profile) == (False, False, None, "prod")


def test_set_language_saves_and_exits(tmp_path):
    config = tmp_path / "config.json"
    assert cli.main(["--set-language", "Norwegian", "--config", str(config), "--out", str(tmp_path / "out")]) == 0
    assert load_config(config)["language"] == "Norwegian"
    assert not (tmp_path / "out" / "mock").exists()  # nothing was run


def test_mock_replay_from_the_command_line(tmp_path):
    out = tmp_path / "out"
    assert cli.main(["--replay", str(FIXTURES), "--mock", "--config", str(tmp_path / "c.json"),
                     "--out", str(out)]) == 0
    assert len(list((out / "mock" / "summaries").glob("2*.md"))) == len(list(FIXTURES.glob("*.json")))


def test_mock_once_from_the_command_line(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "Fetcher", lambda delay_seconds: FakeFetcher(_pages()))
    out = tmp_path / "out"
    assert cli.main(["--once", "--mock", "--config", str(tmp_path / "c.json"), "--out", str(out)]) == 0
    assert len(list((out / "mock" / "summaries").glob("2*.md"))) == 1


def test_without_once_the_polling_loop_starts(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "run_forever", lambda *args: calls.append(args[-1]))
    cli.main(["--mock", "--profile", "test", "--config", str(tmp_path / "c.json"), "--out", str(tmp_path)])
    assert calls == [30]  # the test profile's interval


def test_real_run_stops_before_the_model_without_ner(tmp_path, monkeypatch):
    def missing():
        raise RuntimeError("named-entity model(s) not available")
    monkeypatch.setattr(cli, "require_ner", missing)
    monkeypatch.setattr(cli, "OllamaSummariser", lambda *a: pytest.fail("model must not be created"))
    assert cli.main(["--once", "--config", str(tmp_path / "c.json"), "--out", str(tmp_path)]) == 2


def test_ner_is_unavailable_for_an_unknown_language():
    assert names.ner_available("xx") is False  # load error is caught, not raised


# --- the polling loop --------------------------------------------------------------------------

def test_run_forever_survives_a_failed_run(monkeypatch):
    runs, sleeps = [], []

    def flaky(*args):
        runs.append(1)
        if len(runs) == 1:
            raise RuntimeError("site down")
        return []

    def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(pipeline, "run_once", flaky)
    monkeypatch.setattr(pipeline.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        run_forever({}, None, None, None, interval_seconds=30)
    assert len(runs) == 2 and sleeps == [30, 30]  # the error did not stop the loop


# --- the Ollama client -------------------------------------------------------------------------

def test_ollama_request(monkeypatch):
    sent = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "  - A summary.\n"}}

    def post(url, json, timeout):
        sent.update(url=url, body=json)
        return Response()

    monkeypatch.setattr(summarise.requests, "post", post)
    model = OllamaSummariser("http://localhost:11434/", "llama3.2:3b", num_ctx=8192)
    answer = model.summarise("Artikkeltekst.", "English", previous="- Old.", problems=["x: y"], hints=["Hint."])
    assert answer == "- A summary."
    assert sent["url"] == "http://localhost:11434/api/chat"
    body = sent["body"]
    assert body["model"] == "llama3.2:3b" and body["stream"] is False
    assert body["options"] == {"temperature": 0.2, "num_ctx": 8192}
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["system", "user", "assistant", "user"]  # retry: previous answer + problems
    assert "Hint." in body["messages"][1]["content"] and "x: y" in body["messages"][3]["content"]
    assert "think" not in body  # not sent unless configured


def test_ollama_think_flag_and_reasoning_is_stripped(monkeypatch):
    sent = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "<think>\nReasoning.\n</think>\n\n- A summary."}}

    def post(url, json, timeout):
        sent.update(body=json)
        return Response()

    monkeypatch.setattr(summarise.requests, "post", post)
    model = OllamaSummariser("http://localhost:11434", "qwen3.5:9b-q4_K_M", num_ctx=8192, think=False)
    assert model.summarise("Artikkeltekst.", "English") == "- A summary."
    assert sent["body"]["think"] is False


def test_truncate_cuts_long_text_at_a_boundary():
    text = ("Første avsnitt. " * 40) + "\n\n" + ("Andre avsnitt. " * 40)
    cut, truncated = truncate(text, max_tokens=200)  # 600 characters
    assert truncated and len(cut) <= 600 and cut.endswith(".")
    assert truncate("Kort.", 200) == ("Kort.", False)


def test_mock_summariser_reports_no_content():
    assert MockSummariser().summarise("   ", "English") == summarise.NO_CONTENT


# --- pipeline error paths ----------------------------------------------------------------------

class Unreachable:
    name = "llama3.2:3b"

    def summarise(self, *args, **kwargs):
        raise requests.ConnectionError("connection refused")


def test_run_stops_when_the_model_server_is_unreachable(tmp_path):
    store = Store(tmp_path, mock=False)
    assert run_once(CONFIG, FakeFetcher(_pages()), Unreachable(), store) == []
    assert store.state["articles"] == {}  # nothing marked done: retried next run


def test_replay_stops_when_the_model_server_is_unreachable(tmp_path):
    store = Store(tmp_path, mock=False)
    assert run_replay(CONFIG, FIXTURES, Unreachable(), store) == []
    assert store.state["articles"] == {}


def test_replay_needs_saved_inputs(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_replay(CONFIG, tmp_path, MockSummariser(), Store(tmp_path / "out", mock=True))


def test_env_file_sets_ollama_url_but_is_never_saved(tmp_path, monkeypatch):
    from harness.hamar_news import config as cfg
    env = tmp_path / ".env"
    env.write_text("# comment\n\nOLLAMA_URL='http://gpu-box:11434'\nEMPTY=\nnot a pair\n", encoding="utf-8")
    monkeypatch.setattr(cfg, "ENV_PATH", env)
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    path = tmp_path / "config.json"
    assert load_config(path)["ollama_url"] == "http://gpu-box:11434"
    set_language("German", path)
    assert "gpu-box" not in path.read_text(encoding="utf-8")  # values from .env stay out of config.json
    monkeypatch.delenv("OLLAMA_URL")
