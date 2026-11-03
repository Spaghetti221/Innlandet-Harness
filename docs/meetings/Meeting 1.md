# Meeting 1 (Week 40)
Kick-off lecture, 01.10.26, followed by a short meeting on 02.10.26.
Present: Tor Einar Skarderud, Edvard Ulven Refsdal.

## What we did
- Set up the shared GitHub repository `Spaghetti221/Innlandet-Harness` on 01.10 and gave both
  partners access, following step 1 of the week 40 lecture.
- Scaffolded the repository with Claude Code in plan mode, using the prompt from step 2 of the
  lecture. Result (commit `2b7468c`): `README.md` and `SPEC.md` as placeholders, `CLAUDE.md`
  with the project rules, the folders `tasks/`, `harness/`, `eval/`, `fixtures/` and
  `docs/meetings/`, `docs/prompt-log.md`, `.env.example`, `.gitignore`, and
  `.claude/settings.json` denying reads of `.env` and `.venv`.
- Briefly discussed the lecture: the project is a full-semester harness for a recurring
  information task in Innlandet, and finding the problem is part of the assignment.

## Rules we agreed to follow (from `CLAUDE.md`)
- Never edit anything in `eval/` without asking first.
- No personal data in code, fixtures, prompts, logs or outputs.
- Secrets only in `.env`, which is never read by the agent or committed.
- Run outputs go in `out/`, which is git-ignored.

## Before the next lecture (week 40 checklist)
- Both partners push at least once.
- First task through the loop: pick a public source, write `tasks/001-probe.md` and a failing
  check in `eval/`, then let the agent implement it.
- Three candidate problems, each with users, a public source and a definition of success.
- A meeting report every week and a prompt-log line whenever we correct the agent.
