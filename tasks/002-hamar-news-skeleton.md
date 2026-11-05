# Task 002: Hamar news summariser skeleton

> Status: **done 29.10.2026** (member B). Written 05.11 after the work, to record the
> acceptance check it was built against; see `docs/prompt-log-edvard.md`.

## Goal

`harness/hamar_news/` fetches new articles from Hamar kommune's Lokaldemokrati page, strips each
to its article text, summarises it with a local Llama 3.2 3B model via Ollama in a chosen language,
and writes exactly one Markdown summary per article with a link to the original.

## Context

- Source: <https://www.hamar.kommune.no/lokaldemokrati/> (no API, no RSS). Article URLs are a
  single slug under `/lokaldemokrati/`; pages carry `og:type=article` and an
  `<article class="… single-article">` element.
- Model: `llama3.2:3b` through Ollama (`OLLAMA_URL`, default `http://localhost:11434`).

## Constraints

- Do not edit `eval/`. No personal data: never read the page author; replace e-mail addresses
  and phone numbers before the model.
- `--mock` must work with no model installed. Summarise each article only once.

## Acceptance

- `python -m pytest` passes offline.
- `python -m harness.hamar_news --once --mock` writes one summary per article and an index;
  a second run writes nothing new.

## Out of scope

Checking the summaries (task 003).
