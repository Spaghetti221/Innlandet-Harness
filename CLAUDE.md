# Innlandet Harness

Two-person course project building an agentic workflow. See `SPEC.md` for scope.

## Checks

Python 3 standard library only.

- `scripts/check.sh` — probe → `eval/check_probe.py` → summarise with `claude -p` (writes only to `out/`) → `eval/check_summary.py`
- `scripts/check.sh --offline` — same, reading `fixtures/met_hamar.json`

## Rules

- Never edit anything in `eval/` without asking first.
- No personal data in code, fixtures, prompts, logs or outputs.
- Secrets live in `.env` only; never read or commit it. Keep `.env.example` in sync.
- Run outputs go in `out/` (git-ignored).
- Log notable prompts in `docs/prompt-log.md`.
