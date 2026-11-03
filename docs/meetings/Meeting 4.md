# Meeting 4 (Week 44)
Tor Einar Skarderud and Edvard, 29.10.26.

## Choice of problem
We compared these candidates against the brief and the grading (live demo, evaluation harness,
stress testing, novelty, local fit):

| Candidate | Source | Outcome |
|---|---|---|
| Municipal hearings digest (Edvard, 22.10) | Hamar kommune announcements and Elements meeting calendar | Strong, but no feed, and we could not confirm that automated access is allowed. |
| Hazard digest for Hamar | NVE flood/landslide + MET alerts (open APIs) | Built and tested first, then dropped: real warnings were all green on 29.10, so the demo and test set would be mostly synthetic. |
| Public transport disruptions | Entur SIRI-SX, Innlandstrafikk (open, 15 active situations on 29.10, Norwegian only) | Strong, but a narrower need and little judgement for the agent. |
| Rubbish collection (Edvard) | Sirkula | Largely solved already (app, SMS, PDF); no open API. |
| Jobs for international students, public tenders, football fixtures | NAV feed, Doffin, fotball.no | Personal data in job ads, beta API with key, unclear reuse terms. |
| Meeting places against loneliness | Volunteer centre, library, clubs | Important, but no machine-readable sources; would need organisers' consent first. |

**We have not chosen a topic.** We will do more research and come up with a topic we feel is a good
fit for the assignment. During the meeting we built a prototype for the events candidate ("What's On in
Innlandet") to test how it would work; it is described below as input to that decision.

## Prototype tested: events candidate
- One adapter per source, and a registry recording the robots.txt checks.
- First source: Hamar Kulturhus (WordPress API, robots.txt allows all, 87 events).
- Extraction agents run in parallel, one per batch of pages; every date, time, place and price must quote
  its evidence from the page, and code checks it (max 3 attempts with feedback).
- Everything after extraction is plain code, so the site shows only checked facts.
- No personal data: e-mail addresses and phone numbers are removed when a page is read, raw page text is
  not committed, and only title, time, place, price, one sentence and a link are published.
- All project files and the site in English; each event also gets a Norwegian summary.

## Evidence (test cases)
- 4/4 test cases as expected.
- Typical case with agents: dates precision/recall 1.00, start time 5/6, about $0.11 per run.
  "Registrering 16:45 / Middag 17:30" gave 17:30 in one run and no time in the next: a gap in the
  specification and an example of model variance.

## Open issues
- The chain has not yet run on real pages.
- Only one source, in Hamar, so far.
