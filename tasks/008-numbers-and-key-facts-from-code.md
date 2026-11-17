# Task 008: Numbers checked against the source, key facts in the header from code

> Status: **planned**. Answers C2 feedback 1 ("factual accuracy is low").

## Goal

Every number in a summary (amounts, counts, case numbers, postcodes, years) occurs in the
source, and the header shows the deadline and the case number taken from the source by code,
so a reader sees them correctly even when the model gets a bullet wrong.

## Context

- C2 feedback: "Factual accuracy is low; for public announcements, an incorrect summary can be
  worse than having no announcement at all."
- Today only dates are checked against the source (check 7). Eval run 2, HØP: "Hamarlånet loan
  (450 million kroner)", where the source gives the 450 million to start loans from Husbanken.
- `deadline_from_source` already exists in `harness/hamar_news/export.py`; reuse it, do not
  write a second deadline parser.
- Independent check: `eval/check_numbers.py` (committed before this task).

## Constraints

- Do not edit `eval/`. Do not loosen any existing check.
- New header fields, written by code, never by the model:
  `- **Deadline (from source):** 2026-11-18` and `- **Case number (from source):** 25/01234`,
  or `not stated` when the source has none. Never a guess.
- Add a Level 1 check `numbers_in_source` to `harness/hamar_news/check.py` with the same rule as
  `eval/check_numbers.py`, so a failing summary goes back to the model with the number named
  (as task 005 does for sentences).
- The prompt asks the model not to repeat case numbers; they are in the header.

## Acceptance

- Tests: a fake summary with an invented number fails `numbers_in_source` and the retry message
  names that number; the header fields are right for the ten saved notices.
- Red first: `eval/check_numbers.py` fails on a copy of an eval run with one number changed.
- `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --out out/run6`, then
  `python eval/check_summaries.py --out out/run6` and `python eval/check_numbers.py --out out/run6`
  both print PASS. Level 2 by hand against the task 006 keys, compared with the baseline.

## Out of scope

A number that is in the source but attached to the wrong thing (the HØP case). Task 009 targets it.
