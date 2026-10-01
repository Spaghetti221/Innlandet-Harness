# Innlandet Harness

Two-person course project building an agentic workflow. See `SPEC.md` for scope.

## Checks

TBD — no toolchain chosen yet. Update this section when checks exist.

## Rules

- Never edit anything in `eval/` without asking first.
- No personal data in code, fixtures, prompts, logs or outputs.
- Secrets live in `.env` only; never read or commit it. Keep `.env.example` in sync.
- Run outputs go in `out/` (git-ignored).
- Log notable prompts in `docs/prompt-log.md`.
