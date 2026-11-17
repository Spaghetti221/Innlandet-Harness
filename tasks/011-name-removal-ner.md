# Task 011: Name removal with a Norwegian NER model, also in replay

> Status: **planned**. Answers C2 feedback 2: "Name removal relies on a list of names and
> simple patterns."

## Goal

Person names are found by a named-entity model as well as the three heuristics in `names.py`,
in fetched articles and in replayed inputs, and the model's output is checked the same way.
We measure how many planted names each approach catches.

## Context

- `names.py`: a first-name list, a cue phrase, a following contact detail. It misses a name with
  no list match, no cue and no contact detail.
- Gap found 17.11: `run_replay` loads cleaned JSON and never scrubs again, and it trusts the
  stored `names_in_title`. A replayed input with a name in it is never cleaned, so the stress
  test could not test name removal at all.
- Planted, synthetic names: `fixtures/hamar_news/perturbed/`, listed in `eval/perturbations.json`.
- Independent check: `eval/check_perturbations.py`. It uses only the planted list and regex,
  never the NER model, so it does not share the model's blind spots.

## Constraints

- Do not edit `eval/`. Keep the three heuristics; NER is added, not swapped in.
- NER: a spaCy Norwegian Bokmål pipeline (`nb_core_news_sm`, `_md` or `_lg`); only person
  entities are removed. A person checks the model's person label and version before the plan is
  approved, and pins it in `requirements.txt`.
- `run_replay` runs the same scrubbing and recomputes `names_in_title` for every input.
- The output check (check 6) also runs NER on the summary.
- Organisations and places must survive: Bufdir, Teknaconsult, Innlandet fylkeskommune, Hamar
  kommune, Veltvegen, Åkersvika. `responsible_body` depends on them.

## Acceptance

- Red first: `python -m harness.hamar_news --replay fixtures/hamar_news/perturbed --mock --out out/pert`
  then `python eval/check_perturbations.py --out out/pert --mock` fails before this task.
- After: the same commands print PASS, or the names still leaking are listed honestly in
  `docs/name-removal.md` with a table of planted names caught by heuristics only vs. heuristics + NER.
- Tests: the organisations and places above survive scrubbing; the live replay still passes
  `eval/check_summaries.py`.

## Out of scope

Names inside attached PDFs (not fetched). State as a limitation.
