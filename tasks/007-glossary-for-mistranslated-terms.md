# Task 007: Glossary terms for the mistranslations found by hand

> Status: **planned** (member A or B).

## Goal

Add the Norwegian terms the model mistranslated in runs 1–4 and the eval runs to the English
glossary, and check that the English term is used.

## Context

Hand checks (05.11) found the same kind of error again and again, always a Norwegian term:

| Norwegian | Means | Model wrote |
|---|---|---|
| fjernkjøleanlegg | district cooling plant | "fueling station" |
| utenforskap | social exclusion | "being in care", "sent abroad" |
| møblering | furnishing | "eviction" |
| fortau (sykkelveg med fortau) | pavement (cycle path with pavement) | "bridge" |
| åpen kontordag | open office day | "public consultation" |
| offentlig ettersyn | public inspection (already in the glossary) | "public consultation" |
| startlån | housing start loan | "start-up loans for new businesses" |

## Constraints

- Do not edit `eval/`. A new check must not fail correct summaries in the saved inputs.

## Acceptance

- The terms are in `harness/hamar_news/prompts/glossary_en.md`.
- A Level 1 check `glossary_terms`: when a glossary term is in the source and its English term is
  not in the summary, a known wrong translation from the table above fails the summary. Tests.
- Eval run on the saved inputs: none of the wrong translations above; Level 2 by hand reported.
