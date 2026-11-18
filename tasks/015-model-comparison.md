# Task 015: Model comparison: same test set, Llama 3.2 3B vs. a larger model

> Status: **planned**, last task. An experiment, not a repair: does a larger model raise factual
> accuracy, and what does it cost? Answers C2 feedback 1 from the model side.

## Goal

Run the same inputs through the same harness and checks with two models, the current
`llama3.2:3b` and one larger model, and report factual accuracy, check results, attempts,
withheld summaries, time and cost side by side, so the choice of model is a measured decision.

## Context

- The model is set in `config.json` (`"model": "llama3.2:3b"`); `--config` takes another file,
  so a second model needs no code change if it runs in Ollama.
- Factual accuracy is Level 2: scored by hand against the answer keys from task 006. Level 1
  (`eval/check_summaries.py`) and the eval checks only show what code can decide.
- Hand scores so far: 4/10 (05.11), 3/10, then 9/10 after task 013 with the new checks.
- Model variance: the same model gives different text each run (task 012), so one run per model
  is not enough to compare.

## Constraints

- Do not edit `eval/`. Same inputs, prompts, checks and `max_attempts` for both models; only the
  model changes. If a prompt change is needed for the larger model, it is a separate run, reported
  as such.
- Larger model, first choice: a larger model in Ollama, so no text leaves the machine and no key
  is needed. A person checks the exact model tag exists (`ollama list` after `ollama pull`) and that
  it fits in memory before the plan is approved. Put it in `config.model-large.json`.
- Optional third arm, only if time allows: a hosted model through its API. Then the key lives in
  `.env` (never committed, never in prompts or logs), the run has a cost cap, and the report says
  that the notices' text was sent to a third party. This also counts as evidence for safe
  operation (secrets, cost control).
- Blind scoring: the person scoring Level 2 does not know which model wrote a summary. A small
  script copies the summaries into `out/compare/blind/` under random names and keeps the key in
  `out/compare/blind-key.json` until scoring is done.

## Runs

For each model, 3 runs on `fixtures/hamar_news/live-2026-11-05` and `fixtures/hamar_news/perturbed`:

    python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --config config.json --out out/compare/small-1
    python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --config config.model-large.json --out out/compare/large-1

Each run is checked with `eval/check_summaries.py`, `check_numbers.py`, `check_withheld.py`,
`check_perturbations.py` (on the perturbed runs) and `check_evidence.py` if task 009 is done.

## Acceptance

- `docs/model-comparison.md`, written by us, with one table: for each model, mean and range over
  the 3 runs of Level 2 facts correct (blind, against the task 006 keys), Level 1 pass, articles
  needing 2+ attempts, withheld summaries, prompt injection followed (yes/no), seconds per article,
  and cost (0 for local).
- At least three concrete examples where the models differ on a fact, with the source sentence.
- A recommendation with its trade-off: accuracy against time, memory, cost and where the text goes.
  "The small model is good enough with the checks" is a valid result if the numbers say so.
- Raw output of one run per model in the report appendix.

## Out of scope

Fine-tuning, and changing the default model in `config.json` (a separate decision after this task).
