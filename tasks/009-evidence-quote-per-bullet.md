# Task 009: Every bullet backed by a quote from the source

> Status: **planned**. The "evidence-checked extraction" left out of scope in task 005.
> Answers C2 feedback 1.

## Goal

The model returns each bullet together with the Norwegian sentence from the source it is based
on. Code checks that the quote is in the source word for word; a bullet without a valid quote
fails, goes back to the model, and after the last attempt the summary is withheld (task 010).

## Context

- Hand checks found summaries that pass every Level 1 check and are still wrong: the wrong
  planner, an open office day called a public consultation, an impact assessment the source
  rules out, the HØP loan amounts. No code check can see these today.
- The summary is in English and the source in Norwegian, so the quote is in Norwegian and the
  bullet in English. Only the quote is compared with the source.
- Independent check: `eval/check_evidence.py` (committed before this task).

## Constraints

- Do not edit `eval/`. Do not loosen any existing check.
- The model answers in JSON: `{"bullets": [{"text": "...", "quote": "..."}]}`. Use Ollama's
  structured output (`format` in `/api/chat`); a person checks the Ollama docs for the exact
  parameter before the plan is approved. If the JSON does not parse, that is a failed attempt.
- The Markdown summary keeps its format (3–6 flat bullets); the quotes go to
  `<run>/evidence/<slug>.json` in the shape `eval/check_evidence.py` describes.
- A Level 1 check `evidence` in `harness/hamar_news/check.py`: each quote is at least 20
  characters and occurs in the source after quote, dash, whitespace and case normalisation.
  No fuzzy matching. The retry message quotes the bullet and says its quote was not found.
- The mock summariser writes valid evidence (it copies source sentences), so mock runs pass.

## Acceptance

- Tests: a fake answer with an invented quote fails `evidence`, and the retry message names the bullet.
- Red first: `eval/check_evidence.py --out out/eval2` fails (no evidence files).
- Real-model replay into `out/run7`: `eval/check_summaries.py`, `eval/check_evidence.py` and
  `eval/check_withheld.py` all PASS. Report how many summaries were withheld, and Level 2 by
  hand against the task 006 keys, compared with the baseline and with task 008.

## Out of scope

Whether the English bullet says what the quote says. That is Level 2: by hand now, an LLM judge
measured against the hand scores later. State it as a known gap.
