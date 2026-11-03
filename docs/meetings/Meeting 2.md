# Meeting 2 (Week 42)
Met at the lecture on 15.10.26.
Present: Tor Einar Skarderud, Edvard Ulven Refsdal.

## Since the last meeting (week 41, study week)
- The first probe source was changed from Entur to the weather forecast from MET Norway for
  Hamar, the same source as the lecture's demo.
- Tor added task 001 on 07.10 (commit `75301a3`): `tasks/001-probe.md` describes a probe that
  fetches the MET Locationforecast for Hamar and writes `out/probe.json`; `eval/check_probe.py`
  is the acceptance check, committed while it still fails ("red first"); and
  `Edit(/eval/**)` was added to the deny list so the agent cannot change the check.

## Discussed
- The project and possible problem definitions.
- Guidance from Changkyu on how to go on with the project and how to work with Claude Code.

## Decided and done
- Tighter permissions for the agent (commit `161845a`, same day): deny reads of `.env`,
  `.env.local`, `.venv` and `.venv.local`, and deny edits to `.claude/settings.json` and `eval/`.
  The agent should not be able to read secrets, loosen its own rules or change the checks
  that judge its work.

## Open
- Task 001 is specified but not yet implemented.
- We have no shortlist of candidate problems yet.
