# Task 017: Reject inputs that are not a notice, also in replay

> Status: **planned**. Exam section 3.1: the test set needs "at least one case the workflow is
> expected to reject".

## Goal

An input that is not a Lokaldemokrati notice, or has no text to summarise, is rejected before
any text reaches the model, in replay as well as in a live fetch, and the reason is logged.

## Context

- A live fetch already rejects pages that are not single articles (`extract_article` returns None;
  `fixtures/hamar_news/not_article.html` tests it). Replay has no such step: it summarises every
  JSON file it is given.
- Two reject cases in `fixtures/hamar_news/perturbed/`, listed in `eval/perturbations.json` with
  `"expect": "rejected"`:
  - `test-reject-empty-body.json`: a title and no lead or body. A real model may invent a summary.
  - `test-reject-off-section.json`: a page from the library section, not `/lokaldemokrati/`.
- Independent check: `eval/check_perturbations.py` (a rejected input must leave no saved source,
  text or summary).

## Constraints

- Do not edit `eval/`.
- One function decides, used by both the live fetch and replay: the URL is under the
  Lokaldemokrati listing (or is the listing page, for anonymised articles from task 013), and the
  title, lead and body together have at least 20 words. Rejected inputs are logged with the reason
  and recorded in `state.json` as rejected, so they are not retried every pass.
- Rejection happens before `save_source`, so nothing about a rejected input is stored.

## Acceptance

- Red first: `python -m harness.hamar_news --replay fixtures/hamar_news/perturbed --mock --out out/pert`
  then `python eval/check_perturbations.py --out out/pert --mock` reports both reject cases as stored.
- After: no reject failures from `eval/check_perturbations.py`; the log names both inputs and why.
- The ten saved notices in `live-2026-11-05/` are all still summarised (`eval/check_summaries.py`).
- `python -m pytest` passes.
