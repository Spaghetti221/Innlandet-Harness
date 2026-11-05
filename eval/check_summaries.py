"""Evaluation entry point for the Hamar news summaries (Level 1). Exit 0 = PASS, 1 = FAIL.

    python eval/check_summaries.py                 # real run in out/
    python eval/check_summaries.py --mock          # mock run in out/mock/
    python eval/check_summaries.py --out out/replay

Added 05.11.2026 with the group's permission (CLAUDE.md: eval/ is changed only after asking).
The check logic lives in harness/hamar_news/check.py because the pipeline also uses it for
retry with feedback; this file is the fixed entry point the evaluation is run from, so the
command does not change when the harness does.

Level 1 covers what code can decide (format, dates, deadline, names, language, responsible
body; see SPEC.md). Level 2, the facts, is scored by hand against an answer key for now.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.hamar_news.check import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
