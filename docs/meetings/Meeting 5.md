# Meeting 5 (Week 45)
Supervision meeting on Teams with Changkyu Choi (lecturer), 03.11.26, about one hour.
Present: Tor Einar Skarderud, Edvard Ulven Refsdal, Changkyu Choi.

## Topics discussed
We went through the candidates we have worked on so far:

| Candidate | Where we are |
|---|---|
| Public transport disruptions (Entur, Innlandstrafikk) | Researched in week 44; open data, but a narrow need |
| Hazard warnings for Hamar (NVE, MET) | Built and tested in week 44, then dropped: all warnings were green, so the demo would be mostly synthetic |
| Culture calendar ("What's On in Innlandet") | Prototype built in week 44 from Hamar Kulturhus; every date, time and place must quote its evidence from the page, checked by code. We think it compares well with existing calendars |
| Hamar kommune "Lokaldemokrati" news | Edvard's scraper and local-model summariser from 29.10, now the walking skeleton |

## What we learned
- **Build a digital prototype.** Something that runs and can be shown says more than a plan.
- **Have a storyline.** The demo and the report should tell one story: who has the problem,
  what the workflow does, how we know the output is correct, and what broke and how we fixed it.
- **We may build on top of existing things.** A problem does not have to be unsolved to be
  worth working on; we can add value on top of existing services and sources. This changes
  our earlier criterion from week 44, where we dropped candidates (for example rubbish
  collection) because they were "largely solved already".

## Decision
We continue with the **news app for local politics**: the Hamar Lokaldemokrati summariser is our
Compulsory 2 project. It may grow to include other sources or features later ("amongst other
things"), but the C2 skeleton is built around this one path.

## Status of the project the same day
- Skeleton runs end to end: fetch the listing → extract the article text → remove contact
  details and names → summarise with Llama 3.2 3B (Ollama) → store one Markdown file per
  article → check every summary with code (exit 0/1).
- Respecting the source: robots.txt sets `Crawl-delay: 5`; the code waited 2 s. Fixed.
- First real run: 11 articles in 74 s, **6/11** passed the check. Reading the summaries
  ourselves we found names of a contact person and prize winners, "pumpestasjon" translated
  as "power station", and a check bug that let an indented sub-list pass.
- Repairs: stricter prompt, English glossary, names removed before the model, articles whose
  title names people are rejected, new checks for sub-points, repeats and names.
- Second real run: **5/10** passed (the prize article was rejected). Names, translation and
  repeats were fixed; sub-points remained in the five articles that contain a list.
- Next repair: the harness now checks each answer right away and gives the problems back to
  the model for up to three attempts; a deadline check was added. 40 offline tests pass.
- Open question: keep the local model (free, private) or add the Claude API as a second model
  and compare them on the same saved pages.

## Action points
| What | Who | When |
|---|---|---|
| Third real run with the retry loop; record pass rate and extra calls | Tor | 05.11 |
| Decide on Ollama only, or Ollama plus Claude API | Both | 05.11 |
| Read and rewrite the C2 report in our own words; fill in the human decisions in the prompt log | Both | 05.11 |
| Commit, push and submit Compulsory 2 | Both | 06.11 |
| Plan the demo storyline and the digital prototype for weeks 46–47 | Both | 08.11 |
