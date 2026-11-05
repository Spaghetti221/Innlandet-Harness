"""CLI: python -m harness.hamar_news [--once] [--mock] [--replay DIR] [--profile test|prod] [--language X]"""

import argparse
import logging
import sys
from pathlib import Path

from .config import CONFIG_PATH, REPO_ROOT, interval_for, load_config, set_language
from .fetch import Fetcher
from .pipeline import run_forever, run_once, run_replay
from .store import Store
from .summarise import MockSummariser, OllamaSummariser


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m harness.hamar_news",
        description="Fetch new Hamar kommune 'lokaldemokrati' articles and summarise them.",
    )
    p.add_argument("--once", action="store_true", help="run a single pass and exit")
    p.add_argument("--mock", action="store_true", help="use a fake summariser instead of Ollama")
    p.add_argument("--replay", type=Path, metavar="DIR",
                   help="summarise saved inputs from DIR (e.g. fixtures/hamar_news/live-2026-11-05) "
                        "instead of fetching the site; runs once")
    p.add_argument("--profile", default="prod", help="interval profile from config.json (prod, test)")
    p.add_argument("--interval", type=int, help="override the polling interval in seconds")
    p.add_argument("--language", help="set the summary language (saved to config.json), then run")
    p.add_argument("--set-language", metavar="LANGUAGE", help="save the summary language and exit")
    p.add_argument("--config", type=Path, default=CONFIG_PATH, help="path to config.json")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "out", help="output directory")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(args.out / "run.log", encoding="utf-8")],
    )
    log = logging.getLogger("hamar_news")

    new_language = args.set_language or args.language
    if new_language:
        set_language(new_language, args.config)
        log.info("Summary language saved: %s", new_language)
        if args.set_language:
            return 0

    config = load_config(args.config)
    interval = args.interval or interval_for(config, args.profile)
    summariser = (MockSummariser() if args.mock
                  else OllamaSummariser(config["ollama_url"], config["model"], config["num_ctx"]))
    log.info("Mode: %s | profile: %s | language: %s",
             "mock" if args.mock else f"ollama {config['model']}", args.profile, config["language"])

    fetcher = Fetcher(delay_seconds=config["request_delay_seconds"])
    store = Store(args.out, mock=args.mock)
    try:
        if args.replay:
            written = run_replay(config, args.replay, summariser, store)
            log.info("Done: %d new summaries in %s", len(written), store.summaries_dir)
        elif args.once:
            written = run_once(config, fetcher, summariser, store)
            log.info("Done: %d new summaries in %s", len(written), store.summaries_dir)
        else:
            run_forever(config, fetcher, summariser, store, interval)
    except KeyboardInterrupt:
        log.info("Stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
