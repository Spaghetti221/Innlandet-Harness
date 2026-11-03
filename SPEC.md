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

An output is correct when `python -m harness.hamar_news.check` passes for it:

1. Exactly one summary per article in `state.json`; no duplicates, no orphan files.
2. The header has title, Published, Original article, Summary language and Model.
3. The link is the article's own `https://www.hamar.kommune.no/lokaldemokrati/<slug>` URL.
4. Published and Expires equal the dates in the saved source page.
5. The summary has 3–6 flat Markdown bullet points, none repeated (real runs).
6. No e-mail addresses, phone numbers or personal names in the title or summary.
7. Every date in the summary also appears in the source text (nothing invented).
8. A deadline in the source (a date after "frist", "innen" or "senest") is in the summary.

The pipeline runs checks 5–8 right after the model answers and gives failures back to the
model for up to three attempts in total.

Planned for the exam (not yet built): an LLM-as-judge check that the summary is in the
requested language, translates terms correctly and covers the deadline, and a fixed test
set from saved pages, including the rejected prize article.

## Constraints

- Public source only; robots.txt (including `Crawl-delay`) is honoured; no personal data
  is stored on purpose: authors are never read; e-mails, phone numbers and personal names
  are replaced before storage and before the model; articles whose title names people
  are rejected and remembered only as a hash. Known gap: names are found by a first-name
  heuristic, which can miss rare names.
- A local model (Llama 3.2 3B via Ollama), so no article text leaves the machine.
- Summaries are not published anywhere automatically; a person reads them first.

## Out of scope

Council meeting documents (Elements), PDFs attached to articles, other municipalities.
