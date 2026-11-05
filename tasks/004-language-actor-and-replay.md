# Task 004: Language and responsible-body checks, no raw HTML, saved inputs

> Status: **done 05.11.2026** (member A). Written the same day, after the work.

## Goal

Turn the two repeated errors found by hand in run 3 into Level 1 checks, stop storing raw HTML,
keep every model attempt, and make runs reproducible offline.

## Context

- Hand check of run 3: responsible body wrong in 3/10 summaries (Hamar kommune named where the
  county, a consultancy or Bufdir acts); one summary in Norwegian although English was requested.
- The raw HTML stored in `out/html/` contained names and contact boxes.

## Constraints

- Heuristics must be transparent and tested; no model in the check.
- Saved inputs must contain no personal data.

## Acceptance

- `python -m pytest` passes, including `language`, `responsible_body`, every attempt stored,
  no `*.html` in the output, and no personal data in `fixtures/hamar_news/live-2026-11-05/`.
- `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --mock --out out/replay`
  then `python eval/check_summaries.py --mock --out out/replay` prints PASS.
- Rescoring archived run 3 with the new checks gives 6/10.

## Out of scope

Fixing the actor error in the model's answer (task 005).
