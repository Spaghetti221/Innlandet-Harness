# Spec: Hamar lokaldemokrati summaries (Hamar Reader)

## Problem

Hamar kommune publishes public hearings, plan notices, grant calls and council decisions on
<https://www.hamar.kommune.no/lokaldemokrati/>. The page has no RSS feed, no e-mail alerts, no
API and no notifications, and every article is in Norwegian. Articles are taken down when they
expire. Residents who do not check the page regularly, or who do not read Norwegian well, miss
deadlines for comments and applications. Keeping up is recurring manual work: open the page,
find what is new, read it, and pass on the deadline.

The source is small: 10–16 live notices at a time (16 on 22.10, 11 on 05.11) and one or two new
ones a week. The test set therefore grows by saving each new notice (see *Test set*).

## Users

- Residents of Hamar, including international residents and students who read English better than Norwegian.
- Neighbourhood associations and voluntary organisations that follow plans and grant calls.
- Anyone who relays municipal notices to others (newsletters, notice boards).

## What the workflow produces

For every new article:

- one Markdown summary in the chosen language: title, publish and expiry dates, a link to the
  original, 3–6 bullet points, and links to the saved source and extracted text;
- the cleaned source as JSON (names, e-mail addresses and phone numbers replaced; never the raw HTML);
- every model attempt, with the problems the check found;
- an `INDEX.md` of all summaries, and on request a JSON export for the Hamar Reader app.

## Definition of success

Success has two levels. A run is successful only if both pass.

### Level 1: form and safety, checked by code on every run

`python eval/check_summaries.py --out <run>` exits 0 only if every summary passes:

1. Exactly one summary per article in `state.json`; no duplicates, no orphan files.
2. The header has title, Published, Original article, Summary language and Model.
3. The link is the article's own `https://www.hamar.kommune.no/lokaldemokrati/<slug>` URL.
4. Published and Expires equal the dates in the saved source.
5. The summary has 3–6 flat Markdown bullet points, none repeated (real runs).
6. No e-mail addresses, phone numbers or personal names in the title or summary.
7. Every date in the summary also appears in the source text (nothing invented).
8. A deadline in the source (a date after "frist", "innen" or "senest") is in the summary.
9. The summary is in the requested language (English or Norwegian).
10. The summary does not say Hamar kommune acts when the source names another body as acting.

The pipeline runs checks 5–10 right after the model answers. A failing summary goes back to
the model with the problems, quoting the failing sentence where there is one, for up to three
attempts in total; a summary that still fails is marked "read before use".

### Level 2: facts, checked against an answer key

Why: a summary can pass every Level 1 check and still be wrong (03.11: the wrong planner, an
open office day called a "public consultation", an impact assessment the source rules out).

For each article in the test set we write by hand: who is responsible, what is happening,
where, what residents can do, the deadline and the case number. A summary passes if every
statement it makes about these is supported by the key and none contradicts it.

Target for the exam: no unsupported statement about the deadline or the responsible body, and
at most one summary in ten with any other unsupported statement. Scored by hand now; a
one-command score is task 006, and an LLM judge is planned on top, measured against the hand
scores, with its prompt and failure modes documented.

Results of every run so far are in the report (`report/c2/`, Table 2).

## Test set

- `fixtures/hamar_news/live-2026-11-05/`: the ten notices live on 05.11, cleaned, run offline
  with `python -m harness.hamar_news --replay <dir> --out <run>`. New notices are added as they
  appear, so the set outlives the live page.
- Planned (task 006): answer keys, boundary cases (a very long notice, one without a deadline)
  and reject cases (a page that is not an article, an article whose title names people), all
  synthetic, with no real names.

## Constraints

- Public source only; robots.txt (including `Crawl-delay`) is honoured.
- No personal data stored on purpose: authors are never read; the raw HTML is not stored;
  e-mails, phone numbers and personal names are replaced before storage and before the model;
  articles whose title names people are rejected and remembered only as a hash. Names are found
  by three heuristics (a known first name, a phrase that introduces a person, a following contact
  detail), which can still miss a name; the name check and the export filter are the second line.
- Saved inputs keep only what the evaluation needs: title, lead, body text and dates.
- A local model (Llama 3.2 3B via Ollama), so no article text leaves the machine.
- Summaries are not published anywhere automatically; a person reads them before export.

## Out of scope (Compulsory 2)

Council meeting documents (Elements), PDFs attached to articles, and other municipalities.
Other municipalities in Innlandet with a similar notice page (for example Løten) are a possible
extension for the exam.
