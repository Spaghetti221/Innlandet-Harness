# Task 010: Withhold a summary that still fails, instead of "read before use"

> Status: **planned**. Smallest task; answers C2 feedback 1 directly: "an incorrect summary
> can be worse than having no announcement at all."

## Goal

A summary that still fails its checks after the last attempt is not shown. The summary file
and the export keep the title, dates and link, and say there is no summary; the model's text
is kept only in `attempts/` for us to read.

## Context

- Today `Store.write_summary` writes the failing text with "read before use", and
  `export.py` exports its bullets with `passedCheck: false`, so the app shows it.
- Eval run 2: HØP failed `summary_shape` after 3 attempts and was still shown.
- Independent check: `eval/check_withheld.py` (committed before this task). It fails on
  `out/eval2` today: red first.

## Constraints

- Do not edit `eval/`.
- A withheld summary's Summary section is the line
  `_No summary: the automatic summary did not pass the checks after N attempts. Read the original article._`
  and its header says `- **Check:** withheld after N attempt(s)`. No bullet points.
- `state.json` keeps `passed_check: false`; the export gives `"withheld": true` and no bullets.
- Add `--mock-bad`: a fake summariser that always breaks the checks (Norwegian text with an
  invented date). It uses mock storage like `--mock`.

## Acceptance

- `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --mock-bad --out out/bad`
  then `python eval/check_withheld.py --out out/bad --mock --mock-bad-run` prints PASS.
- Real-model replay: `python eval/check_withheld.py --out out/run6` prints PASS, and with
  `--export <the app's JSON>` after an export.
- `python -m pytest` passes.

## Out of scope

How the app shows a withheld item (a plain "no summary" text is enough).
