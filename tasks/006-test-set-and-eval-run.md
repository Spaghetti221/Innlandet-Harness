# Task 006: Test set with answer keys, and one-command evaluation

> Status: **planned** (member B), due 08.11 (demo frozen).

## Goal

A fixed test set and one command that prints Level 1 and Level 2 scores for a run.

## Context

- Inputs: the ten saved notices in `fixtures/hamar_news/live-2026-11-05/`, plus boundary cases
  (a very long notice, a notice without a deadline) and reject cases (a page that is not an
  article, an article whose title names people; synthetic, no real names).
- Level 2 (`SPEC.md`): for each article a hand-written key with who is responsible, what is
  happening, where, what residents can do, the deadline and the case number.

## Constraints

- Ask before editing `eval/`. Keys are written by a person, not by the agent.
- Keep the hand scores of runs 3 and 4 reproducible from the keys (4/10 and 3/10).

## Acceptance

- `eval/keys/<slug>.json` for every test article, reviewed by both members.
- One command (e.g. `python eval/run_eval.py --out out/run5`) prints Level 1 per check, and
  Level 2 per article as supported / unsupported statements, with totals.
- Reject cases are rejected, and the command exits 1 when Level 1 fails.

## Out of scope

The LLM judge (after the demo).
