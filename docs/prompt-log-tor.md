# Prompt log — Tor

This log records how I worked with coding agents on the project: the prompt, what the agent
did, how the result was verified, and where agent output was **corrected**, **challenged** or
**rejected**. For the 03.11 sessions each entry also gives a *better prompt in hindsight*: how I
would write the same request now, knowing what went wrong. On 04.11 I sent those better prompts to
the agent for real; the last entry records that session. The original prompts were written in
Norwegian; they are translated here without changing their content.

**Tools:** Claude (Opus 5.5) in the Claude app, with access to the repository folder on my Mac;
Claude Code in the terminal.

## Overview

| Date | Type | Event | Outcome |
|---|---|---|---|
| 15.10 | Challenged | Plan for task 001 treated the cache and the saved fixture as one thing | Plan revised before approval |
| 15.10 | Corrected | Practice repo: User-Agent set in a browser fetch, which browsers drop | Fetching moved to Python with a real User-Agent |
| 21.10 | Corrected | Practice repo: weather icons linked to a URL on api.met.no that does not exist | Icon set vendored; check that every image is local |
| 29.10 | Rejected | Hazard digest (NVE + MET) built end to end, 5/5 cases | Dropped: all real warnings were green |
| 29.10 | Corrected | Source notes written from a summary, not from a real page | Replaced with general rules |
| 29.10 | Corrected | Adapter stored full page text and suggested committing it | Contact details removed in code; raw pages git-ignored |
| 03.11 | Flagged by agent | robots.txt sets `Crawl-delay: 5`; the code waited 2 s | Fetcher obeys the site's delay |
| 03.11 | Flagged by agent | Prize article stored winners' names in title and URL | Such articles rejected; nothing stored |
| 03.11 | Corrected | First real run: names, mistranslation, repeated filler; 6/11 passed | Prompt, glossary, name removal, new checks |
| 03.11 | Corrected | The agent's own check accepted an indented sub-list | Check fixed |
| 03.11 | Corrected | The agent claimed a summary had lost its deadline; it had not | Claim withdrawn after checking the file |
| 03.11 | Flagged by agent | Run 3 passed 10/10, but a contact name leaked (first name not in the list) | Two new name rules; run 3 is 9/10 |
| 03.11 | Flagged by agent | Run 3: a passing summary named the wrong planner and claimed an assessment the source rules out | Documented; needs claim-level checks |
| 03.11 | Challenged | "Why Ollama? Isn't Claude better?" | Proposal to support and compare both; decision open |
| 03.11 | Challenged | "Where did meeting 4 go?" | Found on `main`; copied to the branch |
| 03.11 | Corrected | A failed `git show` left an empty `Meeting 4.md` | Replaced with the real file and compared |
| 04.11 | Corrected | The runs table compared pass rates measured with different check versions | Rescored with the final check: 5/11, 5/10, 9/10 |
| 04.11 | Flagged by agent | Full fact check of run 3 (better prompt, sent for real): 12 unsupported statements, wrong body in 3/10, one summary in the wrong language | Strict Level 2: 4/10; report undercounts |
| 04.11 | Flagged by agent | Raw HTML with names and contact boxes stored in `out/html/` | Fixed 05.11: cleaned JSON instead |
| 05.11 | Corrected | Run 3's wrong body and wrong language were invisible to code | Two new Level 1 checks; rescored runs 5/10, 2/10, 6/10 |
| 05.11 | Flagged by agent | Run 4: Level 1 up to 8/10, Level 2 down to 3/10; a retry introduced a false statement | Feedback must quote the failing sentence |

---

## 2026-10-15 to 2026-10-29 — Task 001 and early Compulsory 2 work

**Tool:** Claude in the Claude app (practice repository `weather-demo-live`), Claude Code.

### What happened

1. **Task 001, choice of source.** I moved from MET Norway to Entur and back to MET. The agent
   noticed that the task file committed in the repository did not match the source we were
   discussing, and that the coding agent's plan treated the response cache and the saved fixture
   as the same thing. I sent the critique back to the coding agent and approved only the
   revised plan.
2. **User-Agent in the browser (corrected).** The agent set a `User-Agent` header in a browser
   `fetch`. Browsers do not send it, so MET's terms were broken without any error. Fetching was
   moved to Python with an identifying User-Agent and `Expires`-based caching.
3. **Icon URL that does not exist (corrected).** The agent linked weather icons to an api.met.no
   path that returns nothing. The MIT-licensed icon set was vendored, and a check that every
   image is a local file was added and tested red first.
4. **Task 001 done (29.10).** `harness/probe.py` and `scripts/check.sh`; online, cached, 304 and
   offline runs all passed (commit `38ed2aa`).
5. **Hazard digest (rejected).** The agent built a digest of NVE flood/landslide and MET warnings
   that passed 5/5 cases. Every real warning that day was green, so a demo and a test set would
   be synthetic. Dropped; the code is kept in the practice repository's history.
6. **Events prototype (corrected).** The agent wrote source notes about a page's layout from a
   summary instead of a real page (replaced with general rules), and stored full page text while
   suggesting it be committed, although pages can contain staff contact details (contact details
   now removed in code; raw pages git-ignored). It read "Registrering 16:45 / Middag 17:30" as a
   17:30 start in one run and gave no time in the next; kept as a known ambiguity and an example
   of model variance.

### Outcome

The probe task passed on `main`. Two candidate problems were built far enough to test and then
set aside for stated reasons.

---

## 2026-11-03 — Running the skeleton and starting Compulsory 2

**Tool:** Claude in the Claude app, with access to `~/PycharmProjects/Innlandet-Harness`.

### Prompt (translated)

> I need help opening this file in PyCharm and running it:
> `python3 -m harness.hamar_news --profile test --mock`

Followed by a screenshot of `ModuleNotFoundError: No module named 'bs4'`, and then:

> Read the assignment text for C2. [...] Look in the course project. [...] Moved. Start C2.

When asked, I chose the Hamar news summariser as the topic; a report draft, a finished
skeleton, and a schedule with risks as the outputs; and the retake deadline (06.11).

### What the agent did

1. Explained that the code is a package that must be run as a module from the repository root,
   and that the error came from a missing virtual environment. After `python3 -m venv .venv`,
   `source .venv/bin/activate` and `pip install -r requirements.txt`, the mock run worked on the
   Mac (11 articles found).
2. Searched for the assignment text in the repository and Google Drive, then read the full brief
   once the chat was moved into the course project.
3. **Flagged:** `hamar.kommune.no/robots.txt` sets `Crawl-delay: 5` and disallows `ClaudeBot`.
   The code obeyed `Disallow` but waited only 2 s between requests. The fetcher now waits the
   longer of its own delay and the site's `Crawl-delay` (test: `tests/test_politeness.py`).
4. Added `harness/hamar_news/check.py`, a code-only check of every summary (exit 0/1), with tests
   for failing cases: invented date, contact details, wrong link, orphan file, empty run.
5. Moved the system prompt into the context file `harness/hamar_news/prompts/summarise_system.md`.
6. Filled in `SPEC.md` and drafted the LaTeX report in `report/c2/`.
7. **Flagged for a human decision:** the Hamarprisen article stores the winners' names in its
   title and URL, which conflicts with the no-personal-data rule.

### Verification

`python -m pytest`: 29 passed. `python -m harness.hamar_news.check --mock`: 11/11 PASS.

### Outcome

Skeleton complete in mock mode. Open questions: names in titles (resolved below) and whether
automated reading of the site is acceptable given the `ClaudeBot` rule (to be asked of the
lecturer; fallback is saved snapshots).

### Better prompt (in hindsight)

> The repository is `~/PycharmProjects/Innlandet-Harness`, branch `feature/hamar-news-summariser`.
> 1. Set it up on macOS: create `.venv`, install `requirements.txt`, run
>    `python -m harness.hamar_news --once --mock`, and explain any error. Do not change code.
> 2. Read the Compulsory 2 section of `project_KIUA_2003.pdf`. List what the skeleton is missing
>    against the four technical-minimum requirements and the source constraints, including the
>    site's robots.txt and terms.
> 3. Add a code-only output check (exit 0/1) with failing test cases, fill in `SPEC.md`, and draft
>    the report in the NeurIPS preprint template: English, 3–4 pages, with problem, definition of
>    success, architecture, a schedule working back from the demo in weeks 46–47, risks and the
>    repository link.
> Do not edit `eval/`. Do not commit. Log this session in `docs/prompt-log-tor.md`.

---

## 2026-11-03 (evening) — First run with the real model, and repairs

**Tool:** Claude in the Claude app; Ollama with `llama3.2:3b` on the Mac.

### Prompt (translated)

> How do I run it with the real model?

Followed by the output of the check (6/11 passed), and "Yes" to the repairs the agent proposed.

### What the agent did

1. Gave the steps to install Ollama, pull `llama3.2:3b` and run the harness without `--mock`.
2. Read all failing summaries and reported problems the check had missed:
   - a contact person's full name in one summary and the prize winners' names in another,
     although the prompt forbade names;
   - *pumpestasjon* translated as "power station" and as "wastewater treatment plant" instead of
     "pumping station";
   - one summary repeating "Affected area / What residents can do: None mentioned" five times.
3. **Corrected its own check:** the first version stripped indentation before counting bullets,
   so a summary with an indented sub-list had passed.
4. Archived the run in `out/archive/2026-11-03_run1_llama3.2-3b/` (git-ignored; contains names).
5. Implemented the repairs: a stricter prompt (one flat list, at most six points, no names of any
   person, no statements that something is missing); an English glossary of planning terms;
   removal of names before the model (`names.py`); rejection of articles whose title names people,
   remembered only as a hash; checks for sub-points, repeated bullets and names.

### Verification

11 articles in 74 s; 6/11 passed the first check. After the repairs: 37 tests passed; replaying
the 11 saved pages through the repaired pipeline with the mock model, the prize article was
rejected, no names were stored and 10/10 summaries passed.

### Outcome

All problems found by hand now have a repair and, except the mistranslation, a code check.
Mistranslation needs a judge for meaning, planned for the exam.

### Better prompt (in hindsight)

> Run 1 with `llama3.2:3b` passed 6/11 (output below). Before changing anything, archive the run.
> Then read every summary, including those that passed, and list problems the check missed.
> For each problem, propose a repair and a check that would catch it next time. Do not loosen
> any existing check. Show me the list before implementing.

---

## 2026-11-03 (late evening) — Second run, deadline check and retry with feedback

**Tool:** Claude in the Claude app; Ollama with `llama3.2:3b`.

### Prompt (translated)

Output of `python -m harness.hamar_news --once --out out/run2` and the check (5/10 passed), then:

> Yes, do it. But why are we using Ollama? Isn't it better to use Claude?

### What the agent did

1. Compared run 2 with run 1. Fixed: no names, "pumping station" correct, no repeated filler.
   Not fixed: sub-points, in exactly the five articles whose source contains a list.
2. **Corrected:** it first claimed the Tjuvholmen summary had lost its deadline (6 November). It
   had read the summaries with lines cut at 170 characters, and the date was at the end of a long
   line. The claim was withdrawn after a direct search of the file.
3. Added a `deadline_kept` check: a date after *frist*, *innen* or *senest* in the source must be
   in the summary.
4. Added retry with feedback: the checks run right after the model answers; on failure the model
   receives its answer and the list of problems, up to three attempts in total. Attempts are
   recorded in each summary file and in `state.json`.
5. **Challenged by me — Ollama or Claude:** the agent compared the two on quality, cost, privacy
   and exam requirements, and suggested supporting both behind a `--provider` option and
   comparing them on the same saved pages, as a model-variance stress test.

### Verification

`python -m pytest`: 40 passed, including tests for a missing deadline, a retry that repairs a
summary, and retries that stop and flag. Replay with the mock model: 10/10.

### Outcome

Run 2 archived in `out/archive/2026-11-03_run2_llama3.2-3b/`. Next: a third real run with the
retry loop. Choice of model: open, to be decided with Edvard.

### Better prompt (in hindsight)

> Run 2 passed 5/10 (output below). Compare runs 1 and 2 article by article: what improved, what
> did not, what got worse. Verify every claim against the full file, not truncated output. Then
> add a check that the source's deadline is kept and a retry loop that gives check failures back
> to the model (at most 3 attempts), with tests. Separately, compare Ollama and the Claude API on
> quality, cost per run, privacy and the exam's cost-control requirement, without changing code.

---

## 2026-11-03 (late evening) — Third run: retry works, reading the output finds more

**Tool:** Claude in the Claude app; Ollama with `llama3.2:3b`.

### Prompt

Output of `python -m harness.hamar_news --once --out out/run3` and the check: 10/10 passed.

### What the agent did

1. Before accepting the result, read every retried summary in full (lines not truncated,
   following the lesson from run 2) and compared the suspicious ones with the source text.
2. **Flagged:** the Veltvegen summary names the person who answers questions about the plan. The
   first name was not in our list, so the name was neither removed before the model nor caught by
   the check. Added two rules: capitalised words after a phrase that introduces a person ("rettes
   til", "kontaktperson er", "contact person") and before a contact detail ("…, epost:").
   Company names ending in AS/IKS are excluded. With the new rules run 3 scores **9/10**.
3. **Flagged, not fixable by code:** the Ringgata summary passed every check but states that Hamar
   kommune is the planner (it is Innlandet fylkeskommune), calls an open office day at the county
   hall a "public consultation" at the city hall, and claims an environmental impact assessment
   that the source says is *not* required. Its dates and case number are correct.
4. Archived the run in `out/archive/2026-11-03_run3_llama3.2-3b_retry/` and updated the report
   with a table of all three runs.

### Verification

Retry log: 6 of 10 articles failed the first attempt; 5 passed on the second and 1 on the third
(17 model calls, 123 s). The deadline check caught a real omission (Ringgata, attempt 1).
`python -m pytest`: 41 passed. Replay of saved pages with the mock model: 10/10, no names stored.

### Outcome

Retry with feedback fixes format. It does not make facts right: the Ringgata summary is wrong in a
way no format or date check can see. For the exam, extraction must quote evidence for who, what
and where, checked against the source, and a judge must compare meaning.

### Better prompt (in hindsight)

> Run 3 passed 10/10 (output below). Do not trust the number. Read every summary in full and
> compare each statement with the source text: who is responsible, what is happening, where,
> and when. List every statement that is not supported by the source, even if all checks passed.

---

## 2026-11-03 (night) — Meeting reports and the missing meeting 4

**Tool:** Claude in the Claude app.

### Prompts (translated)

> Make a good meeting report out of these notes and include details from the project so far: [notes]

> Where did meeting 4 go?

> Read and upgrade meeting reports 1–3.

### What the agent did

1. Wrote `docs/meetings/Meeting 5.md` from my notes, keeping what was said in the meeting separate
   from the project status. Attendance and the owners of action points are the agent's
   assumptions and are marked for me to confirm.
2. **Challenged by me:** meeting 4 had been committed to `main` on 29.10, after our feature branch
   was created, so it never reached the branch. The agent copied it over.
3. **Corrected:** its first `git show` used a branch without the file. The command failed, but the
   shell redirect had already created an empty `Meeting 4.md`. The agent replaced it with the real
   file and compared it with the copy in my other clone.
4. Expanded meetings 1–3 from the commit history, the lecture slides and the prompt logs, adding
   nothing without a source.

### Outcome

Five meeting reports on the branch. Before submitting we must merge `main` into the branch and
the branch into `main`.

### Better prompt (in hindsight)

> Meeting 4 is missing from `docs/meetings/` on this branch. Find where it is (branches, remotes,
> other clones) and explain why, without changing any files. Then propose how to bring it in.

---

## 2026-11-04 — Evaluating and improving the report

**Tool:** Claude in the Claude app, in the course project.

### Prompts (translated)

> Evaluate the report against the assignment text and the grading criteria.

> Do it, and improve the report based on the evaluation.

### What the agent did

1. Compared the report with the Compulsory 2 requirements and the five grading criteria.
2. **Corrected its own earlier work:** the runs table compared pass rates measured with three
   different versions of the check. Rescored all three archived runs with the final check:
   5/11, 5/10, 9/10 (previously reported as 6/11, 5/10, 10/10).
3. Pointed out that the definition of success ("passes the code check") contradicted the
   wrong-fact summary that passed. Rewrote it as two levels: code checks on every run, and facts
   against a hand-made answer key on a fixed test set.
4. Checked the source: the Lokaldemokrati page has no RSS feed, e-mail subscription or
   notification, only social media links. Added a "What exists already" paragraph.
5. Traced the wrong-fact failure through the stages and noted that earlier attempts are not
   stored, so we cannot tell whether the retry introduced the errors.
6. Added the export and app to the figure, owners to the schedule, raised the access risk to
   medium, and added references (RFC 9309, Ollama, Llama 3.2, Expo, Maynez et al. 2020,
   Zheng et al. 2023), each checked to exist.

### To confirm (human)

The Level 2 targets and the owner of each milestone are the agent's proposals.

### Better prompt (in hindsight)

> Evaluate the report as a strict examiner against the brief and each grading criterion. For every
> number in the report, check that it was measured the same way as the numbers it is compared with.

---

## 2026-11-04 (evening) — The better prompts, sent for real

**Tool:** Claude in the Claude app, with access to the repository folder on my Mac.

After the earlier sessions I wrote better versions of my prompts (the "Better prompt (in
hindsight)" sections above). On 04.11 at 22:25 I sent them to the agent in one message, so this
entry records them as actual prompts. Some of the work they ask for had already been done; the
agent re-checked it instead of rebuilding it.

### Prompts (as sent)

> The repository is ~/PycharmProjects/Innlandet-Harness, branch feature/hamar-news-summariser.
> 1. Set it up on macOS: create .venv, install requirements.txt, run
>    python -m harness.hamar_news --once --mock, and explain any error. Do not change code.
> 2. Read the Compulsory 2 section of project_KIUA_2003.pdf. List what the skeleton is missing
>    against the four technical-minimum requirements and the source constraints, including the
>    site's robots.txt and terms.
> 3. Add a code-only output check (exit 0/1) with failing test cases, fill in SPEC.md, and draft
>    the report in the NeurIPS preprint template [...]. Do not edit eval/. Do not commit. Log this
>    session in docs/prompt-log-tor.md.

> Run 1 with llama3.2:3b passed 6/11 (output below). Before changing anything, archive the run.
> Then read every summary, including those that passed, and list problems the check missed. For
> each problem, propose a repair and a check that would catch it next time. Do not loosen any
> existing check. Show me the list before implementing.

> Run 3 passed 10/10 (output below). Do not trust the number. Read every summary in full and
> compare each statement with the source text: who is responsible, what is happening, where, and
> when. List every statement that is not supported by the source, even if all checks passed.

> Meeting 4 is missing from docs/meetings/ on this branch. Find where it is (branches, remotes,
> other clones) and explain why, without changing any files. Then propose how to bring it in.

> Evaluate the report as a strict examiner against the brief and each grading criterion. For
> every number in the report, check that it was measured the same way as the numbers it is
> compared with.

### What the agent found

**Setup and gaps (prompt 1).** The agent works in a Linux environment against my folder, not on
macOS, and the municipal site is not reachable from there (proxy 403), so the mock run fails there
with a network error, not a code error; on my Mac it ran on 03.11. 47 offline tests pass. The check,
`SPEC.md` and the report already existed, so nothing was rebuilt. The four technical-minimum
requirements are met; the weak point is that only one stage calls the model. Gaps against the
source constraints:
- `robots.txt` allows all agents with `Crawl-delay: 5` (obeyed) but disallows `ClaudeBot`.
- The privacy page says nothing about reuse, automated access or copyright; no terms found.
- **New: raw HTML is stored unchanged** in `out/html/`, including names and contact boxes. The
  text sent to the model is cleaned, but the saved page is not, which conflicts with "must not
  store information that identifies individuals". Same for the archived runs. Not yet fixed.
- The User-Agent names the project but gives no contact address or repository URL.

**Run 1 reviewed again (prompt 2).** Problems the check of the time missed, with repair and check:

| Problem | Repair | Check | Status |
|---|---|---|---|
| Names in two summaries | Remove names before the model; reject articles about named people | `no_personal_names` | Done 03.11 |
| *pumpestasjon* as "power station" / "wastewater treatment plant"; *sykkelveg med fortau* as "bike path with a bridge" | Glossary; add *fortau* = pavement | For each glossary term in the source, the English term (or the Norwegian word) is in the summary | Glossary done; *fortau* and the check new |
| Sub-points | Retry with feedback | `summary_shape` (flat list) | Done 03.11 |
| Filler: "None mentioned", "not specified" | Prompt rule 4 | Repeated bullets (done); new: flag "not mentioned / not specified" | Partly done |
| **Invented ways to take part in decided cases**: three decisions said residents "can comment" | Prompt: for decisions, say whether it can be appealed | If the title is a decision (*vedtatt*, *godkjent*), the summary must not say residents can comment, submit or attend | New |
| A processing time ("up to 5 working days") labelled as the deadline | — | A bullet that says "deadline" must contain a date | New |
| The check accepted indented sub-lists | Fixed in the check | Test `test_sub_points_fail` | Done 03.11 |

Nothing was implemented, as asked.

**Run 3 fact-checked in full (prompt 3).** Every statement in all ten summaries compared with the
source. Unsupported or contradicted statements:

1. *Ringgata*: says Hamar kommune is the planner; it is Innlandet fylkeskommune.
2. *Ringgata*: "bike lane along the existing road"; the source says a cycle path with a pavement.
3. *Ringgata*: a "public consultation (høring)" on 10.11 at "Hamar City Hall (Fylkeshuset)"; the
   source describes an open office day at the county hall.
4. *Ringgata*: the municipality "will conduct environmental impact assessments"; the source says
   no impact assessment is required.
5. *Veltvegen*: "the municipality of Hamar is starting the planning work"; a consultancy (the
   proposer) is, as the summary itself says in its last bullet.
6. *Veltvegen*: names the contact person (privacy; caught by the new name rules).
7. *Tilskudd*: "Hamar municipality is launching a funding scheme"; it is a national scheme run by
   Bufdir with the municipalities.
8. *Tilskudd*: "individuals must set themselves up in the regulation"; the source tells applicants
   (organisations) to read the rules.
9. *Tjuvholmen*: calls *offentlig ettersyn* a "public consultation (høring)" although the glossary
   says "public inspection".
10. *Mindre endring*: "also available at the municipal council meeting" is garbled; the source
    points to the case documents and minutes of that meeting.
11. *Bolig*: **the whole summary is in Norwegian**, although English was requested.
12. *Bolig*: the lease "must" run at least three years; the source says the municipality *wishes* so.

No unsupported statements in four summaries (HØP, water and sewerage hearing, centre plan,
development agreements). Every deadline was correct (10/10). **Strict Level 2 score: 4/10.** The
responsible body is wrong in 3/10, always replaced by "Hamar municipality" when another body acts,
so run 3 fails the report's own Level 2 target. The wrong language passed Level 1 because no check
looks at the language.

**Meeting 4 (prompt 4).** Committed to `main` on 29.10 (`d408803`). Our branch was created from
`1b4cfd9`, before that commit, and the two branches have since diverged (4 commits each). The file
was copied to the branch on 03.11 (`5da8b48`) with identical content. Proposal: `git merge
origin/main` into the branch, then a pull request from the branch into `main`. Files unchanged.

**Strict examiner and numbers (prompt 5).** Checked against the source of each number:
- Consistent: Level 1 scores (one final check for all runs), 74/91/123 s (all from the "Mode" to
  the "Done" log line), 17 calls = 10 + 7 retries, six first-attempt failures, 16 and 11 listed
  articles, 16 glossary terms, 8 prompt rules, 47 tests, 3-day reminder.
- Not comparable: run 1 time covers 11 articles, runs 2–3 cover 10. Per article: 6.7, 9.1 and
  12.3 s. Run 2 was slower than run 1 without any retries, which the report does not explain.
- "About 7 s per article" includes the 5 s crawl delay, so it is not model time.
- The report says one passing summary had wrong facts; the full check above finds three with the
  wrong responsible body and one in the wrong language. **The report undercounts.**
- Level 2 has a target but no reported result; the hand score is now 4/10 and should be reported.
- Remaining examiner points: the text is still agent-written; the repository must be reachable
  and `main` must contain the code; the template must match the one on Canvas.

### Outcome

No code or report changed in this session; only this log. The findings above are input for the
next changes: a language check, an actor check, storing cleaned pages instead of raw HTML, and an
honest Level 2 result in the report.

---

## 2026-11-05 — Turning the hand check into repairs

**Tool:** Claude in the Claude app, with access to the repository folder on my Mac.

### Prompt (translated)

> Yes, and update prompt-log-tor.md and the report.

This answered the agent's proposal after the previous session: a language check, a check of the
responsible body, cleaned source data instead of raw HTML, and an honest Level 2 result in the report.

### What the agent did

1. **Language check** (`language` in Level 1): counts common English and Norwegian words and fails
   a summary written in the wrong one of the two. It catches the Norwegian summary from run 3.
2. **Responsible-body check** (`responsible_body`): finds bodies the source names as acting
   ("Innlandet fylkeskommune kunngjør", "Teknaconsult starter", "administreres av Bufdir") and fails
   a summary that says Hamar municipality is doing it. On the ten run 3 sources it found exactly the
   three bodies the hand check found, and nothing in the other seven.
3. **No raw HTML stored:** the run now saves the cleaned article and its dates as
   `source/<slug>.json`; the check reads that. Old runs' HTML is still read so they can be rescored.
4. **Every attempt stored** in `attempts/<slug>/attempt-N.md`, with the problems found.
5. Rescored the three archived runs with the new checks: Level 1 = **5/10, 2/10, 6/10**. The
   actor and language errors were already in run 2, so they appeared when the prompt was made
   stricter, not with the retry.
6. Report: two new rows in the Level 1 table, the runs table with Level 2 (4/10 for run 3) and time
   per article, the hand-check findings and the failure trace, a new milestone, risks updated, and
   an appendix excerpt of the session where the better prompts were sent. Main text still 4 pages.

### Verification

`python -m pytest`: 51 passed (new: language, responsible body, every attempt stored, no raw
HTML). Rescoring the archived runs as above.

### Outcome

The two repeated errors are now caught by code. The remaining error of meaning in run 3 (a claimed
impact assessment) is left for Level 2 and the evidence-checked extraction stage. The raw HTML
already in `out/html/` and in the archives still contains names and should be deleted when the old
runs are no longer needed. The heuristics are narrow (three verbs and a word list) and are named
as such in the report.

---

## 2026-11-05 (night) — Run 4: better checks, not better facts

**Tool:** Claude in the Claude app; Ollama with `llama3.2:3b` on the Mac.

### Prompt

The log of `python -m harness.hamar_news --once --out out/run4` (attached as a file, no text).

### What the agent did

1. Ran the check on run 4: **8/10** on Level 1 (20 model calls, 134 s, 13.4 s per article).
   Ringgata and tilskudd still fail `responsible_body` after three attempts.
2. Read the stored attempts for those two. In all three attempts the model kept the same first
   sentence ("The Hamar municipality is launching ...") and only added the right body elsewhere.
   The feedback names the problem but not the sentence, so the model does not know what to change.
3. Read the eight passing summaries against the sources (same standard as run 3). Every deadline
   was right and the actor error in Veltvegen was fixed on attempt 3, but new unsupported statements
   appeared: *startlån* (a housing loan) became "start-up loans for new businesses"; the water and
   sewerage plan was said to focus on "reducing the environmental impact" of ageing infrastructure;
   a rental "must" run three years (the source says the municipality wishes so); "the council
   meeting can be attended" in a decided case. **Strict Level 2: 3/10.**
4. Searched the stored attempts: "the council meeting can be attended" appears only in attempt 2,
   so **a retry introduced it**. First direct evidence that retries can make facts worse.
5. Archived the run in `out/archive/2026-11-05_run4_llama3.2-3b_allchecks/` and added run 4 to
   the report (table row and a paragraph), keeping the main text at 4 pages.

### Outcome

Level 1 rose from 6/10 to 8/10 while Level 2 fell from 4/10 to 3/10. Optimising for the checks did
not improve the facts. Next: retry feedback that quotes the failing sentence and names the body the
source gives; then the evidence-checked extraction stage.

### Better prompt (in hindsight)

> Here is the log of run 4. Run the check, read the stored attempts of every summary that needed a
> retry, and tell me for each retry whether it fixed the problem, left it, or introduced a new one.
> Then hand-check all summaries against the sources with the same standard as run 3.

---

## Lessons

1. **Read the output, not only the check.** The first check passed summaries with names and
   wrong translations; every new check came from reading the output by hand first.
2. **Verify the agent's claims, including claims about its own work.** Its check had a bug, it
   reported a missing deadline that was not missing, and it left an empty file. All three were
   found by checking the files directly.
3. **A prompt alone does not control a small model.** The 3B model kept nesting lists after the
   prompt forbade it; feedback from code checks fixed that in run 3.
4. **A passing check is not a correct summary.** Run 3 passed 10/10, yet one summary named the
   wrong planner and contradicted its source. Format and dates can be checked by code; facts need
   evidence quotes and a judge.
5. **Say what not to do.** The better prompts above add "do not change code", "do not loosen
   checks", "verify against the full file" and "show me before implementing". Those limits would
   have prevented most of the corrections in this log.
