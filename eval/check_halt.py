"""Task 016 check: the kill switch halts exactly when a run crosses its limits.

    python eval/check_halt.py --out out/bad --mock
    python eval/check_halt.py --out out/run6 --export app/src/data/<export>.json

Recomputes the two kill-switch conditions from the run itself, without harness code:
- withheld ratio: articles with passed_check false / all articles in state.json
- model calls: files in <root>/attempts/<slug>/ (attempt-N.md and title-attempt-N.md), one per call
Limits come from config.json (halt_withheld_ratio, max_model_calls_per_article).

PASS when <root>/HALT.json exists if and only if a limit is crossed, and its reason names the
crossed limit. With --export: a halted run must not have produced that export file.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _run import articles, report, roots

DEFAULTS = {"halt_withheld_ratio": 0.3, "max_model_calls_per_article": 4}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--config", type=Path, default=Path("config.json"))
    ap.add_argument("--export", type=Path)
    a = ap.parse_args()
    _, root = roots(a.out, a.mock)

    cfg = json.loads(a.config.read_text(encoding="utf-8")) if a.config.exists() else {}
    limits = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
    state = articles(root)
    n = len(state)
    withheld = sum(1 for rec in state.values() if not rec.get("passed_check", True))
    calls = sum(1 for p in (root / "attempts").glob("*/*.md")
                if p.name.startswith(("attempt-", "title-attempt-")))

    crossed = []
    if n and withheld / n > limits["halt_withheld_ratio"]:
        crossed.append("withheld")
    if n and calls > limits["max_model_calls_per_article"] * n:
        crossed.append("model_calls")

    halt_file = root / "HALT.json"
    errors = []
    print(f"articles {n}, withheld {withheld}, model calls {calls}, limits {limits}, crossed {crossed or 'none'}")
    if crossed and not halt_file.exists():
        errors.append(f"limit crossed ({', '.join(crossed)}) but there is no {halt_file}")
    if not crossed and halt_file.exists():
        errors.append(f"{halt_file} exists but no limit is crossed")
    if crossed and halt_file.exists():
        reason = json.loads(halt_file.read_text(encoding="utf-8")).get("reason", "")
        if not any(c.split("_")[0] in reason for c in crossed):
            errors.append(f"HALT.json reason {reason!r} does not name the crossed limit {crossed}")
    if crossed and a.export and a.export.exists():
        errors.append(f"the run is halted but the export {a.export} was written")
    return report(errors)


if __name__ == "__main__":
    sys.exit(main())
