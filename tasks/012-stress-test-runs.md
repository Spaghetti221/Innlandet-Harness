# Task 012: Stress test: repeated runs before and after the repairs

> Status: **planned**. Exam section 3.3 (the primary emphasis): inject, observe, repair, prove
> the repair holds through the evaluation harness.

## Goal

One script runs the real model N times on the saved and the perturbed inputs, for any git ref,
and runs every check on each run, so the baseline and the repaired system can be compared on
the same inputs for two perturbation classes: input perturbation and model variance.

## Context

- Input perturbation: `fixtures/hamar_news/perturbed/` (planted names, an injected instruction to
  move the deadline to 1 January 2030, names in a title). The injected date is in the source, so
  check 7 (dates in source) cannot catch it: a blind spot to show, not hide.
- Model variance: Llama 3.2 3B gives different text each run (temperature 0.2).
- Baseline: the tag `eval-baseline` (set after task 006, before 008). Repairs: tasks 008–011.

## Constraints

- Do not edit `eval/`.
- `scripts/stress.sh <git-ref> [runs]` (default 5) uses a `git worktree` for the ref, so the
  working tree is not touched, and writes each run to `out/stress/<ref>/run-<i>/`.
- Every run is checked with the checks from the current `eval/` (not the ref's), so both refs are
  judged by the same rules: `check_summaries.py`, `check_numbers.py`, `check_evidence.py`,
  `check_withheld.py`, `check_perturbations.py`.
- One line per run and check in `out/stress/<ref>/results.csv`: ref, run, check, exit code, and
  passed/total from `check.json` where there is one.
- Offline input only; the model is the only live part.

## Acceptance

- `scripts/stress.sh eval-baseline 5` and `scripts/stress.sh main 5` finish and write `results.csv`.
- `docs/stress-test.md`, written by us: both tables side by side; for each failure, how it moved
  through the stages (fetch → clean → model → check → retry → withhold or export) and why the
  repair stops it; failures that remain, stated as such.
- Copy one full evaluation run's raw output to the report appendix (exam requirement).

## Out of scope

Dependency failure (Ollama down) and context degradation, unless we choose them instead.
