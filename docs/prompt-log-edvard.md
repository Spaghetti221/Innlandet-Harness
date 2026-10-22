# Prompt log — Edvard

## 2026-10-22 — Problem candidates for Compulsory 2

**Tool:** Claude Code (Opus 5.5), plan mode, then execution after approval.

### Prompt

> Read the "Compulsory 2" section on page 2 and find two real and relevant community problems in Hamar, Norway. Generate problem definitions, and compare them with each other, as well as a third problem definition I've thought of — rubbish collection, and identify the problem with the most potential/material. Do not write any code yet, but log this interaction to a new prompt_log_edvard.txt file or something in the repository.

### What the agent did

1. Extracted the text of pages 1–3 of `project_KIUA_2003.pdf` with `pdftotext`, because the PDF reader lacked poppler. It used the technical minimum (checkable output, several stages, tools, at least one automated part, more than a single prompt), the constraints (no personal data, respect the sources, fit the local context) and the exam's later needs (a reject case in the test set, stress testing, approval gates) as criteria.
2. Checked official sources (pages as of 2026-10-22):
   - Hamar kommune announcements and hearings: https://www.hamar.kommune.no/lokaldemokrati/ (16 HTML articles, Norwegian only, no RSS feed; they mix open hearings with deadlines, decision notices and prizes).
   - Council meeting calendar (Elements): https://prod02.elementscloud.no/publikum/970540008_PROD-970540008/Dmb
   - Shared culture calendar: https://www.hamar.kommune.no/kulturkalender/ (about 2,055 entries, no iCal, RSS or API, some stale entries).
   - Hamar kulturhus programme: https://www.hamar-kulturhus.no/program/ (no feed).
   - Sirkula IKS: https://www.sirkula.no and https://www.sirkula.no/hjemme-hos-deg/finn-dine-tommedager/tommekalender-for-hele-aret (address lookup, PDF, SMS and the Min renovasjon app; holiday shifts are already covered; Norwegian only; no open API).

### Problem definitions

- **P1: Municipal hearings digest.** Residents, neighbourhood associations and international residents miss hearings, because the notices are buried, in Norwegian and spread across pages. The workflow runs weekly. It fetches the announcements, classifies each as a hearing, a decision or information, and extracts the deadline, the area and the plan ID. It summarises them in plain Norwegian and in English, and outputs a digest plus an iCal file of deadlines. A human approves before anything is published.
- **P2: Deduplicated weekly "what's on in Hamar" (English).** The workflow merges the shared kulturkalender with the venue programmes, normalises them to one schema, removes duplicates, flags stale entries, and produces an English digest for students.
- **P3 (my idea): Rubbish collection.** It would turn Sirkula's collection, holiday-shift and sorting information into translated, checked reminders and sorting answers for newcomers.

### Comparison (condensed)

| Criterion | P1 Hearings | P2 Events | P3 Rubbish |
|---|---|---|---|
| Recurring need | Weekly, hard deadlines | Weekly, high volume | Weak (yearly calendar, stable rules) |
| Already solved? | No | Partly (the shared calendar) | Largely (app, SMS, PDF) |
| Source access | Open public HTML and documents | No feeds, scraping risk | No API, address lookups |
| Stages | Fetch → classify → extract → summarise and translate → check → publish | Fetch → normalise → dedup → digest | Thin, close to a single prompt |
| Checkable output | Strong (dates, links, plan IDs, iCal) | Good (dedup precision and recall) | Weak |
| Reject case | Non-hearings, expired hearings | Stale or past events | Unclear |
| Stress testing | Prompt injection in documents, layout drift, long PDFs | Outage, format drift | Little to perturb |

### Outcome

The agent recommended **P1, the municipal hearings digest**, as having the most potential and material. P2 is the fallback. P3 is the weakest on its own, because existing services already cover the core need and the sources are closed. Sirkula news could at most become an extra P1 source later.

**Decision pending:** the problem will be chosen together with my project partner, and `SPEC.md` has not been changed. No code was written.
