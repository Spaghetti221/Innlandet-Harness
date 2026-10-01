# Innlandet Harness

Two-person course project building an agentic workflow. Details TBD — see [SPEC.md](SPEC.md).

## Layout

| Path | Purpose |
|---|---|
| `SPEC.md` | Problem, users, definition of success |
| `tasks/` | Task definitions for the workflow |
| `harness/` | The agent harness (no code yet) |
| `eval/` | Evaluation cases and scoring — do not edit without agreement |
| `fixtures/` | Test inputs (no personal data) |
| `docs/meetings/` | Meeting notes |
| `docs/prompt-log.md` | Log of prompts used during development |
| `out/` | Run outputs (git-ignored) |

## Setup

Copy `.env.example` to `.env` and fill in the values. `.env` is never committed.
