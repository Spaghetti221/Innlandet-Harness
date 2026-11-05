# Innlandet Harness

Two-person course project building an agentic workflow. See `SPEC.md` for scope.

## Checks

Python 3.11+ with a venv in `.venv/` (`pip install -r requirements.txt`).

Hamar news summariser (`harness/hamar_news/`):
- Tests: `python -m pytest` (offline, synthetic fixtures)
- Smoke run without a model: `python -m harness.hamar_news --once --mock`
- Output check (exit 0/1): `python eval/check_summaries.py --mock`
- Eval run, offline: `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --mock --out out/eval` then `python eval/check_summaries.py --mock --out out/eval`
- Tasks with acceptance checks: `tasks/`

MET probe from task 001 (`harness/probe.py`, Python standard library only):
- `scripts/check.sh` — probe → `eval/check_probe.py` → summarise with `claude -p` (writes only to `out/`) → `eval/check_summary.py`
- `scripts/check.sh --offline` — same, reading `fixtures/met_hamar.json`

## Rules

- Never edit anything in `eval/` without asking first.
- No personal data in code, fixtures, prompts, logs or outputs.
- Secrets live in `.env` only; never read or commit it. Keep `.env.example` in sync.
- Run outputs go in `out/` (git-ignored).
- Log notable prompts in `docs/prompt-log.md`.
