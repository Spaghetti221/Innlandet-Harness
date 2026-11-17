# Task 014: Translated article titles

> Status: **implemented 17.11, real-model acceptance run pending** (Edvard).

## Goal

Titles stayed Norwegian while the summaries were translated, so a reader who does not read
Norwegian could not tell the notices apart in the list or the app.

## Decision

The title is translated **in its own model call** (option A), not in the summary call (option B):

- The title gets its own check and retries. In B a bad title would force the whole summary to be
  rewritten, and the 3B model already breaks the bullet format on first attempts.
- The summary check stays unchanged (every line a `- ` bullet); B would need a parser and a new
  failure mode for a missing or misplaced title line.
- The call is short (about one second) and the title prompt can be strict about one line.
- The file name keeps the slug: the check, `state.json`, the export and links use it as the key.

## What changed

- `prompts/translate_title_system.md`; `summarise.title_messages`, `needs_title_translation`,
  `OllamaSummariser.translate_title`, `MockSummariser.translate_title`.
- `check.clean_title` (format only) and `check.title_problems`: one line, translated, at most
  about twice as long, no names, no dates not in the original title, no own placeholders, glossary.
- `pipeline.translate_title_checked`: up to `max_attempts`, feedback on retry; if none passes or
  the call fails, the Norwegian title is kept. A lost model server stops the run as before.
- Summary header: translated title, then `- **Original title:**`; attempts in `title-attempt-N.md`;
  `state.json` gets `title_translated`; `INDEX.md` shows it; the check verifies it (SPEC check 13).
- Export: `summaries.<lang>.title`; the app shows it with `titleFor()` (list, detail, share,
  reminders) and the Norwegian title below the heading.

## Acceptance

- `python -m pytest` passes (`tests/test_title.py`).
- A replay with the real model (`--replay fixtures/hamar_news/live-2026-11-05 --out out/eval-009`)
  passes `python eval/check_summaries.py --out out/eval-009`, and the titles read as English.
- The app shows English titles with English selected (`npm start`, after the export).
