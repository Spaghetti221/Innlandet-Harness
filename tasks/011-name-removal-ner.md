# Task 011: Replay cleans like a live fetch; measure name removal

> Status: **planned**. Answers C2 feedback 2 ("Name removal relies on a list of names and
> simple patterns") together with task 013, which added the NER layer.

## Goal

Replayed inputs go through the same cleaning and anonymisation as fetched articles, so the
perturbed fixtures actually test name removal, and we can report, with numbers, what the list
and patterns catch and what NER adds.

## Context

- Task 013 (Edvard, 17.11) added spaCy NER to `names.py`, with `accept_ner_span` filters
  against false alarms (no lowercase words, single words only if a known first name), and
  anonymises articles whose title names people (`anon-<hash>` slug).
- Gap: `run_replay` loads saved JSON through `load_saved_article` and never cleans again, and
  it trusts the stored `names_in_title`. `--replay fixtures/hamar_news/perturbed` therefore
  stores and summarises the planted names untouched.
- Measured 18.11 on four synthetic, realistic-looking names (`eval/perturbations.json`):

  | Planted name | list + patterns (`eval-baseline`) | + NER (task 013) |
  |---|---|---|
  | after a cue, first name in the list | removed | removed |
  | no cue, first name not in the list | **leaks** | removed |
  | lower case | **leaks** | **leaks** |
  | hyphenated first name | removed | removed |
  | names in a title | detected | detected |

- First attempt (17.11) used invented names ("Testa Fiktivsen"); the Norwegian model labelled
  them ORG, so they measured the model's idea of a name, not removal. Planted names must look
  like real Norwegian names.
- Independent check: `eval/check_perturbations.py` searches every file the run wrote.

## Constraints

- Do not edit `eval/`. Do not loosen the NER filters from task 013 without a measured reason.
- Cleaning happens in one place: replay calls the same function as `extract_article`
  (scrub title, lead and body; recompute `names_in_title`; anonymise the slug and URL).
- Synthetic names only in fixtures and tests.

## Acceptance

- Red first: `python -m harness.hamar_news --replay fixtures/hamar_news/perturbed --mock --out out/pert`
  then `python eval/check_perturbations.py --out out/pert --mock` fails (names in every file).
- After: the same commands leave only the known lower-case leak, or nothing. Any name still
  leaking is listed in `docs/name-removal.md` with the table above, re-measured.
- Decide and write down what to do about lower-case names (accept the leak, or a rule that
  does not bring back the false alarms from task 013), with the false-alarm count either way.
- `python -m pytest` passes; the live replay still passes `eval/check_summaries.py`.

## Out of scope

Names inside attached PDFs (not fetched). State as a limitation.
