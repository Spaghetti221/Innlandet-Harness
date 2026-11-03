# Meeting 3 (Week 43)
Met at the lecture on 22.10.26 ("Context, simulation, orchestration, automation").
Present: Tor Einar Skarderud, Edvard Ulven Refsdal.

## Discussed
- The project, the problem definitions and how to proceed. Compulsory 2 (report and walking
  skeleton) is due 30.10, so we need to choose a problem soon.

## Work done the same day
Edvard asked Claude Code to read the Compulsory 2 section of the brief and compare problem
candidates (logged in `docs/prompt-log-edvard.md`):

| Candidate | Source | Assessment |
|---|---|---|
| P1 Municipal hearings digest | hamar.kommune.no/lokaldemokrati, council calendar | Weekly need with hard deadlines; not solved elsewhere; checkable output (dates, links, plan IDs) |
| P2 Weekly "what's on in Hamar" | Shared culture calendar, venue programmes | High volume, partly solved by the shared calendar; no feeds |
| P3 Rubbish collection (Edvard's idea) | Sirkula | Largely solved already (app, SMS, PDF); no open API; close to a single prompt |

The agent recommended P1, with P2 as the fallback.

## Decision
- None yet. We did not accept the recommendation directly: we want to choose the problem
  together and check whether automated access to the municipal site is allowed.
- `SPEC.md` stays empty until the problem is chosen.

## Also done
- Meeting reports updated and the first prompt logs added (commits `b5e527f`, `1b4cfd9`).

## Next
- Choose the problem before Compulsory 2.
- Finish task 001 (MET probe) so the check passes on `main`.
