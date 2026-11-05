# Task 005: Retry feedback that quotes the failing sentence

> Status: **done 05.11.2026, accepted** (member A). Baseline, eval run 1 (feedback names only the
> problem): 7/10, all three actor errors left after three attempts. Acceptance run, eval run 2
> (`out/archive/2026-11-05_eval2_task005/`): all three actor errors fixed on the second attempt,
> Level 1 9/10, and the hand check confirms the right body in all three. New failure seen: the
> retries squeezed one summary into a single bullet.

## Goal

When a summary fails `responsible_body` (or another check that points at a sentence), the retry
message quotes the failing sentence and states what the source says, e.g. *"The sentence 'The
Hamar municipality is launching a funding scheme' is wrong: the source says the scheme is
administered by Bufdir. Rewrite that sentence."*

## Context

- Run 4 (05.11): the model kept the same wrong first sentence through all three attempts in two
  of three actor errors; the feedback named the problem but not the sentence.
- Stored attempts: `out/archive/2026-11-05_run4_llama3.2-3b_allchecks/attempts/`.

## Constraints

- Do not edit `eval/`. Do not loosen any check. Feedback must not contain personal names.

## Acceptance

- A test with a fake model shows the failing sentence and the body named by the source in the
  retry message.
- `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --out out/run5` with
  the real model: `responsible_body` passes for at least 2 of the 3 articles where another body
  acts, and the stored attempts show the sentence changed. Report Level 2 by hand as before.

## Out of scope

Evidence-checked extraction of who, what and where (exam version).
