"""Load and save config.json. The summary language persists here between runs."""

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config.json"
ENV_PATH = REPO_ROOT / ".env"

DEFAULTS = {
    "language": "English",
    "ollama_url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "num_ctx": 8192,
    "max_input_tokens": 6000,
    "max_listing_pages": 3,
    "request_delay_seconds": 2,
    "profiles": {
        "prod": {"interval_seconds": 6 * 60 * 60},
        "test": {"interval_seconds": 30},
    },
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(json.dumps(DEFAULTS))  # deep copy
    if path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))
    _load_env_file()
    if os.environ.get("OLLAMA_URL"):
        config["ollama_url"] = os.environ["OLLAMA_URL"]
    return config


def save_config(config: dict, path: Path = CONFIG_PATH) -> None:
    # Never persist values that came from the environment.
    on_disk = json.loads(path.read_text(encoding="utf-8")) if path.exists() else dict(DEFAULTS)
    on_disk["language"] = config["language"]
    path.write_text(json.dumps(on_disk, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def set_language(language: str, path: Path = CONFIG_PATH) -> dict:
    language = language.strip()
    if not language:
        raise ValueError("Language must not be empty")
    config = load_config(path)
    config["language"] = language
    save_config(config, path)
    return config


def interval_for(config: dict, profile: str) -> int:
    try:
        return int(config["profiles"][profile]["interval_seconds"])
    except KeyError:
        raise ValueError(f"Unknown profile '{profile}'; known: {', '.join(config['profiles'])}")


def _load_env_file() -> None:
    """Minimal .env loader (KEY=VALUE lines). Existing environment variables win."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)
