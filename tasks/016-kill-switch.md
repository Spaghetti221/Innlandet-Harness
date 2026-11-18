# Task 016: Kill switch: halt and block export when a run goes wrong

> Status: **planned**. Exam section 3.2 (safe operation): "a measurable condition under which
> autonomous operation is halted, and the mechanism that halts it", plus a cost budget per run.

## Goal

After every pass, the harness measures two things and halts if either crosses its limit: the
share of summaries withheld, and the number of model calls. A halted run writes `HALT.json`
with the reason, exports nothing, and the scheduled loop stops until a person removes the file.

## Context

- Today the harness stops only when the model server is unreachable or a spaCy model is missing.
  Nothing stops a run that produces bad summaries, or a model that keeps failing and retrying.
- Summaries are never published automatically: a person runs the export (human-in-the-loop gate).
  The kill switch protects that gate from a bad run.
- A withheld summary (task 010) is the harness's own signal that something failed: a name, a
  wrong date, the wrong language, an invented number (task 008). Many at once means the model,
  the prompt or the source has changed, not one bad article.
- Model calls per run: `attempts/` holds one file per call (`attempt-N.md`, `title-attempt-N.md`).
  Eval run 2: 19 summary calls for 10 articles.
- Independent check: `eval/check_halt.py` (committed before this task).

## Constraints

- Do not edit `eval/`.
- Limits in `config.json`, with these defaults:
  `"halt_withheld_ratio": 0.3` (halt if more than 30 % of the summaries in a pass are withheld),
  `"max_model_calls_per_article": 4` (halt if a pass uses more than 4 × articles model calls).
- `HALT.json` in the run root (`<out>` or `<out>/mock`):
  `{"reason": "...", "articles": N, "withheld": N, "model_calls": N, "limits": {...}, "time": "..."}`.
- With `HALT.json` present: the export refuses with a clear message and writes nothing; the loop
  (no `--once`) exits with code 3; a new pass refuses to start. Only a person deleting the file
  resumes. No automatic reset.
- The budget is also enforced during the pass: stop calling the model once the budget is used,
  and write `HALT.json` then, not only at the end.

## Acceptance

- Red first: `python eval/check_halt.py --out out/bad --mock` fails on a `--mock-bad` run
  (10/10 withheld, no `HALT.json`).
- `--mock-bad` replay: `HALT.json` with reason "withheld"; `eval/check_halt.py --out out/bad --mock`
  prints PASS; `python -m harness.hamar_news.export --run out/bad --mock` refuses.
- `--mock` replay: no `HALT.json`, `eval/check_halt.py` prints PASS, export works.
- A test with a fake model that always fails and `max_model_calls_per_article: 1` halts on the budget.
- `python -m pytest` passes.

## Out of scope

Alerts (e-mail, chat). The log line and `HALT.json` are enough for the exam.
