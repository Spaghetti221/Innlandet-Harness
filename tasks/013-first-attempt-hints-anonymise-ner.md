# Task 013: First-attempt hints, anonymised articles, named-entity layer

> Status: **implemented 17.11, real-model acceptance run pending** (Edvard).

## Goal

1. Fewer failed first attempts: in the 17.11 live run, 8 of 9 summaries needed a second
   attempt (sub-points / more than 6 bullets, Norwegian instead of English, "Hamar
   municipality" as actor where the source names the county, Bufdir or a consultancy).
2. Summarise articles whose title names people instead of rejecting them.
3. Name removal that does not rely only on a list and patterns (feedback from the lecturer:
   "Name removal relies on a list of names and simple patterns.").

## What changed

- `summarise.build_hints`: after `</article>` the user message repeats the language and the
  flat-list rule, and names the responsible body found by `check.source_actors` (the same rule
  as the `responsible_body` check). The model's text is never rewritten by code.
- Glossary: utleier, leietaker, møblering ("eviction" on 17.11), bosetting, plus the terms
  from task 007.
- `extract_article`: when the title names people, the slug becomes `anon-<hash>` and the URL the
  listing page; the title gets `[name removed]` (`[navn fjernet]` before 18.11). The check accepts the listing link for `anon-`
  slugs. Runs before 17.11 kept rejected articles as hashes in `state.json`; they stay skipped.
- `names.py`: spaCy NER (`PER`/`PERSON`) spans are added to the three heuristics. Real runs stop
  before any text reaches the model if a spaCy model is missing (`require_ner`).

## Second round (17.11, after eval-008 and run-008)

Eval-008 was 6/10 and two of three anonymised live articles were false alarms: the NER model
labelled single place words (Børstad, Stange, Jernbanebrygga, Tjuvholmen), lowercase words
("avløp"), a URL and a street address as people. In the one real case, the second prize winner
(hyphenated first name) stayed in the text: the model labelled it an organisation until the
first name was replaced. The model also wrote "[date]" and left "startlån" untranslated.

- `names.accept_ner_span`: single word only if a known first name (and not "Per 1. januar");
  no lowercase words, numbers, URLs, line breaks or organisation words.
- Rule 1 accepts hyphenated first names; new rule 4: capitalised words joined by "og"/"," to a
  removed name. `scrub_person_names` repeats until a pass finds nothing (max 3).
- Checks `invented_placeholder` and `untranslated` (glossary terms outside brackets); prompt
  rule 9 on placeholders; concrete one-line example in the format hint.
- `Fetcher.get` retries once after a reset connection, waiting the Crawl-delay.
- Eval-008 rescored with the new checks: 9/10 (the one failure is the real "startlån" error).

## Constraints

- No edits in `eval/`. No personal data in fixtures or tests (synthetic names only).
- `pytest` stays offline; NER tests are skipped when the spaCy model is not installed.

## Acceptance

- `python -m pytest` passes.
- `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --out out/eval-008`
  then `python eval/check_summaries.py --out out/eval-008` exits 0, with fewer articles needing
  2+ attempts than the 17.11 live run (8 of 9).
- A live `--once` run summarises the article that was rejected on 17.11, with no name in its
  title, file name, link or saved source.
