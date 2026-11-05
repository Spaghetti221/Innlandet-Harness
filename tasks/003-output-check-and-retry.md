# Task 003: Output check and retry with feedback

> Status: **done 03.11.2026** (member A). Written 05.11 after the work, to record its acceptance
> check; see `docs/prompt-log-tor.md`.

## Goal

A code-only check of every summary (exit 0/1), used both as the evaluation and inside the
pipeline: a summary that fails is sent back to the model with the problems, at most 3 attempts.

## Context

- Checks (Level 1 in `SPEC.md`): one summary per article, header and link, dates match the
  source, 3–6 flat bullets, no contact details or names, no invented dates, deadline kept.
- First real run (03.11): 6/11 passed the first version of the check; reading by hand found
  names, mistranslations and filler the check missed.

## Constraints

- Never loosen a check to make a run pass. Failures report counts of names, never the names.
- Obey the site's `robots.txt`, including `Crawl-delay: 5`.

## Acceptance

- `python -m harness.hamar_news --once --mock && python eval/check_summaries.py --mock` prints PASS.
- Tests show each check failing on a bad summary (`tests/test_check.py`), and a retry repairing one.

## Out of scope

Checking facts (Level 2), language and the responsible body (task 004).
