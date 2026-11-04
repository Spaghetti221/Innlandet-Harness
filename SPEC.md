# Spec: Hamar lokaldemokrati summaries

## Problem

Hamar kommune publishes public hearings, plan notices, grant calls and council decisions on
<https://www.hamar.kommune.no/lokaldemokrati/>. The page has no RSS feed, no API and no
notifications, and every article is in Norwegian. Residents who do not check the page
regularly, or who do not read Norwegian well, miss deadlines for comments and applications.
Keeping up is recurring manual work: open the page, find what is new, read it, and pass on
the deadline.

## Users

- Residents of Hamar, including international residents and students who read English better than Norwegian.
- Neighbourhood associations and voluntary organisations that follow plans and grant calls.
- Anyone who relays municipal notices to others (newsletters, notice boards).

## What the workflow produces

For every new article: one Markdown summary in the chosen language with the title, the
publish date, the expiry/deadline date, a link to the original, 3–6 bullet points, and links
to the saved page and extracted text. An `INDEX.md` lists all summaries.

## Definition of success

Success has two levels. A run is successful only if both pass.

### Level 1: form and safety, checked by code on every run

`python -m harness.hamar_news.check` exits 0 only if every summary passes:

1. Exactly one summary per article in `state.json`; no duplicates, no orphan files.
2. The header has title, Published, Original article, Summary language and Model.
3. The link is the article's own `https://www.hamar.kommune.no/lokaldemokrati/<slug>` URL.
4. Published and Expires equal the dates in the saved source page.
5. The summary has 3–6 flat Markdown bullet points, none repeated (real runs).
6. No e-mail addresses, phone numbers or personal names in the title or summary.
7. Every date in the summary also appears in the source text (nothing invented).
8. A deadline in the source (a date after "frist", "innen" or "senest") is in the summary.
9. The summary is in the requested language (English or Norwegian).
10. The summary does not say Hamar kommune acts when the source names another body as acting.

The pipeline runs checks 5–10 right after the model answers and gives failures back to the
model for up to three attempts in total.

### Level 2: facts, checked against an answer key

Why: on 03.11 a summary passed every Level 1 check but named the wrong planner, turned an open
office day into a "public consultation" and claimed an impact assessment the source rules out.

For each article in a fixed test set of saved pages (typical, boundary and reject cases,
including the rejected prize article) we write by hand: who is responsible, what is happening,
where, what residents can do, the deadline and the case number. A summary passes if every
statement it makes about these is supported by the key and none contradicts it.

Target for the exam: no unsupported statement about the deadline or the responsible body, and
at most one summary in ten with any other unsupported statement. Scored by hand now; an LLM
judge is planned on top, measured against the hand scores, with its prompt and failure modes
documented.

First result (hand check of run 3, 04.11): 4/10 summaries free of unsupported statements;
all deadlines right; responsible body wrong in 3/10; one summary in the wrong language.
The two repeated errors became Level 1 checks 9 and 10.

Run 4 (05.11, checks 9 and 10 in the retry loop): Level 1 8/10, Level 2 3/10. Retries fixed
language and format but not the actor in 2/3, and one retry introduced a false statement.

## Constraints

- Public source only; robots.txt (including `Crawl-delay`) is honoured; no personal data
  is stored on purpose: authors are never read; the raw HTML is not stored; e-mails, phone
  numbers and personal names are replaced before storage and before the model; articles whose title names people
  are rejected and remembered only as a hash. Known gap: names are found by a first-name
  heuristic, which can miss rare names.
- A local model (Llama 3.2 3B via Ollama), so no article text leaves the machine.
- Summaries are not published anywhere automatically; a person reads them first.

## Out of scope

Council meeting documents (Elements), PDFs attached to articles, other municipalities.
