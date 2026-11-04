# Innlandet Harness

Two-person course project (KIUA-2003, INN) building an agentic workflow for the Innlandet region.
The problem, users and definition of success are in [SPEC.md](SPEC.md).

**Quick start (walking skeleton, no model needed):**

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
python -m harness.hamar_news --once --mock           # fetch, extract, summarise (mock)
python -m harness.hamar_news.check --mock            # check the output: prints PASS/FAIL, exit 0/1
```

## Layout

| Path | Purpose |
|---|---|
| `SPEC.md` | Problem, users, definition of success |
| `tasks/` | Task definitions for the workflow |
| `harness/hamar_news/` | The harness: fetch → extract → summarise → store, plus the output check |
| `harness/hamar_news/prompts/` | Context files: the system prompt, and an English glossary of planning terms |
| `harness/hamar_news/data/first_names.txt` | First names used to find and remove personal names |
| `config.json` | Run settings: language, model, intervals, request delay |
| `eval/` | Evaluation cases and scoring — do not edit without agreement |
| `fixtures/` | Test inputs (no personal data) |
| `docs/meetings/` | Meeting notes |
| `app/` | Hamar Reader: Expo phone app that shows the summaries (see [app/README.md](app/README.md)) |
| `report/c2/` | Compulsory 2 report (LaTeX, NeurIPS preprint style): `main.tex`, `main.pdf` |
| `docs/prompt-log.md` | Log of prompts used during development |
| `out/` | Run outputs (git-ignored) |

## Setup

Copy `.env.example` to `.env` and fill in the values. `.env` is never committed.

## Hamar news summariser (`harness/hamar_news`)

Hamar kommune has no API or RSS feed for its "Lokaldemokrati" announcements
(<https://www.hamar.kommune.no/lokaldemokrati/>). This program polls that page, saves
every new article's HTML, strips it down to the raw article text, and asks a local
**Llama 3.2 3B** model (via [Ollama](https://ollama.com)) to summarise it in a language of
your choice. Each article gets **exactly one** Markdown summary file with a link back to
the original, and an `INDEX.md` lists them all.

### How it finds articles

Article pages have no `/article/` prefix, so it filters in two steps:

1. **URL filter:** links on the listing (and up to `max_listing_pages` pagination pages,
   `?offsetNNN=2` …) are kept only if they are on `www.hamar.kommune.no` and look like
   `/lokaldemokrati/<one-slug>` with no query string or `#anchor`.
2. **Page check:** a fetched page is kept only if it has `og:type = article` and an
   `<article class="… single-article">` element. Only the headline, lead
   (`itemprop="description"`) and body (`itemprop="articleBody"`) **inside that element**
   are extracted, which drops menus, footers and contact boxes. The page author is never
   read. E-mail addresses and phone numbers are replaced with placeholders before
   anything reaches the model.

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

For real (non-mock) runs, on the machine that runs the model:

```bash
ollama pull llama3.2:3b
ollama serve                       # listens on http://localhost:11434
```

If Ollama runs elsewhere, set `OLLAMA_URL` in `.env` (see `.env.example`).

### Running

| Command | What it does |
|---|---|
| `python -m harness.hamar_news --once --mock` | One pass, fake summaries (no model needed) |
| `python -m harness.hamar_news --profile test --mock` | Test loop: checks every 30 s, fake summaries |
| `python -m harness.hamar_news --profile test` | Test loop against real Ollama |
| `python -m harness.hamar_news` | **Real run:** checks every 6 h, real Ollama |
| `python -m harness.hamar_news --interval 120 --mock` | Any interval in seconds |
| `python -m harness.hamar_news --set-language Norwegian` | Save the summary language and exit |
| `python -m harness.hamar_news --language German --once` | Save the language, then run |

Switching from testing to a real run means dropping `--mock` and `--profile test`.
The intervals live in `config.json` under `profiles`. Stop the loop with Ctrl+C. Instead of
the built-in loop you can schedule `python -m harness.hamar_news --once` with Windows Task
Scheduler or cron.

### Configuration (`config.json`)

| Key | Default | Meaning |
|---|---|---|
| `language` | `English` | Summary language. Set by `--language` / `--set-language` and used by all later runs |
| `ollama_url` | `http://localhost:11434` | Ollama server (`OLLAMA_URL` overrides it) |
| `model` | `llama3.2:3b` | Ollama model tag |
| `num_ctx` | `8192` | Context window requested from Ollama (see below) |
| `max_input_tokens` | `6000` | Article text is cut (at a paragraph if possible) above this estimate |
| `max_listing_pages` | `3` | How many listing pages to scan per run |
| `request_delay_seconds` | `5` | Pause between requests to hamar.kommune.no (the longer of this and the site's robots.txt `Crawl-delay` is used) |
| `max_attempts` | `3` | Model calls per article, including retries after a failed check |
| `profiles` | `prod` 21600 s, `test` 30 s | Polling intervals |

### Output (`out/`, git-ignored)

```
out/
  html/<slug>.html                        raw page as downloaded
  text/<slug>.txt                         stripped article text (what the model sees)
  summaries/<published-date>_<slug>.md    one summary per article (real runs)
  summaries/INDEX.md                      table of all summaries with links
  state.json                              articles already summarised (never redone)
  mock/summaries/…, mock/state.json       same for --mock runs, kept separate
  run.log
```

Each summary file shows the title, publish date, expiry/deadline date, a link to the
original article, links to the saved HTML and text, the language, the model and the time
it was summarised. An article is marked as done only after its summary file has been
written. If Ollama is down or fails, the article is retried on the next run. Mock runs
keep their own state, so they never stop a real run from summarising an article.

### Context window

Llama 3.2 3B supports up to 128k tokens, but Ollama only gives a model a small context
(2048–4096 tokens, depending on the version) unless `num_ctx` is set. Anything over the
limit is cut silently, and the system prompt or the start of the article can be lost.

The longest article at the time of writing (2026-10-29) was about 510 words, roughly
4 KB of text. That is about 1.2k tokens; the typical article is 150–300 words, about
400–800 tokens. With the system prompt and the answer (≤500 tokens), a
summary needs about 2–2.5k tokens (the English system prompt with its glossary is ~700 tokens). **`num_ctx = 4096` is the minimum that is safe; the
default of 8192 leaves room for long hearing notices.** Text over `max_input_tokens` is
truncated, and the summary file says so.

### Personal data

Before anything is stored or sent to the model, e-mail addresses, phone numbers and
personal names are replaced with placeholders. Names are found by three heuristics: a common
first name from `data/first_names.txt` followed by one to three capitalised words;
capitalised words after a phrase such as "rettes til" or "kontaktperson er"; and
capitalised words right before a contact detail ("…, epost:"). An
article whose **title** names people (for example a prize given to individuals) is
rejected: nothing is stored, and it is remembered only as a hash of its slug.

### Checking the output

```bash
python -m harness.hamar_news.check --mock    # mock run
python -m harness.hamar_news.check           # real run
```

The check reads `state.json`, every summary file and the saved HTML, and fails (exit 1)
if any article breaks a rule: one summary per article, complete header, the link is the
article's own `hamar.kommune.no/lokaldemokrati` URL, Published/Expires match the source
page, 3–6 flat bullet points with none repeated (real runs), no e-mail addresses, phone
numbers or personal names, **no date in the summary that is missing from the source
text**, and **the deadline kept** (a date after "frist", "innen" or "senest" in the source
must be in the summary). Failures report how many names were found, never the names.

### Retry with feedback

The same checks run inside the pipeline right after the model answers. If a summary breaks
a rule, the model gets its previous answer and the list of problems and tries again, up to
`max_attempts` (default 3) in total. Each summary file records the number of attempts, and
a summary that still fails is marked "read before use". Retries cost extra model calls: at
most `max_attempts` per article. Results also go to `check.json`.

### Phone app (Hamar Reader)

`python -m harness.hamar_news.export` turns one or more runs into `app/src/data/summaries.json`
(summaries, dates and links only; summaries in which a name is found are left out). The app in
`app/` shows them in English and Norwegian with reminders before deadlines. Setup and running:
[app/README.md](app/README.md).

### Tests

```bash
python -m pytest
```

The tests run offline against synthetic fixtures in `fixtures/hamar_news/`.
