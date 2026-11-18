# Meeting 6 (Week 47)
Working session, 17.–18.11.26. Present: Tor Einar Skarderud, with Claude (Claude app) and Claude
Code as tools. Edvard was not present; he was told by message, and the open points below are for
our next meeting.

## Topics discussed
The Compulsory 2 feedback:

| Strengths | To improve |
|---|---|
| Effectively identified weaknesses in the Lokaldemokrati page | Factual accuracy is low; for public announcements, an incorrect summary can be worse than having no announcement at all |
| Connected the notification function with the subsequent action | Name removal relies on a list of names and simple patterns |

We turned the feedback into tasks with a red check each, so every repair can be measured before and
after: `docs/c2-feedback-plan.md`, tasks 008–012 and 015–017, checks in `eval/`, perturbed inputs in
`fixtures/hamar_news/perturbed/`. The commit before any repair is tagged `eval-baseline`.

## What we learned
- **A grey summary is better than a wrong one.** A summary that still failed after three attempts
  was shown with "read before use" and exported to the app (HØP in eval run 2). Withholding it
  answers the feedback directly.
- **A PASS on old files is not a PASS.** The first acceptance run for task 010 printed PASS with
  "0 new summaries": the check had read files left from an earlier run. A fresh output directory
  for every run is now part of every acceptance command.
- **Test the test.** The first measurement said name removal caught "0 of 3" planted names. The
  names were invented ("Testa Fiktivsen"), and the Norwegian NER model labelled them organisations,
  so the number measured the test, not the system. With realistic synthetic names: list + patterns
  2/4, with NER (task 013) 3/4; a lower-case name leaks in both.
- **Read the plan before approving it.** Two plans were sent back: task 010 would have let the check
  skip any summary marked "withheld", even one with bullets; task 008 compared numbers with the
  article body only, so a number from the title would have failed.

## Status of the project the same day
- **Task 010 done** (PR #1, merged): failing summaries are withheld (no bullets, title, dates and
  link kept, model text only in `attempts/`); `--mock-bad` added. After rebasing on Edvard's
  tasks 013 and 014: 119 tests; `--mock-bad` 10/10 withheld; `--mock` 10/10 pass. The agent rewrote
  the setup of 8 existing tests; the diff was read and no assertion was removed or weakened.
- **Task 008 done** (PR #2, merged): every number in a summary must be in the source; deadline and
  case number in the header come from code. 125 tests. Real model (`out/run6`): the number check
  caught an invented "500 million NOK" in HØP and the retry fixed it; Level 1 8/10, the two
  failures are untranslated glossary terms ("sentrumsplan", "bestemmelse", "kulturmiljø").
- Both pull requests conflicted with Edvard's tasks 013 and 014 in `check.py`, `store.py`,
  `summarise.py` and the tests. Resolved by keeping both sides; the fake failing model got the
  `hints` parameter the pipeline now passes.
- Tor merged both pull requests himself after reading the diffs and running every check, because
  Edvard could not be reached; Edvard is asked to look at the conflict resolution in `check.py`.
- Found in the real run: the title "Offentlig ettersyn mindre endring av sentrumsplanen" was
  flagged as containing a person's name in all three attempts (likely an NER false alarm), so the
  Norwegian title was kept.

## Open points for the next meeting
- Who writes the answer keys for task 006 (Level 2 for every later number, and for task 015).
- Lower-case names: accept the leak as a trade-off against false alarms, or try a rule.
- The NER false alarm on the "sentrumsplanen" title, and "sentrumsplan" failing all three attempts.
- Order of the remaining tasks before the white paper (03.12, 11:59).

## Action points
| What | Who | When |
|---|---|---|
| Pull `main`; check the conflict resolution in `check.py` | Edvard | next session |
| Real-model run on `main` (`out/run7`) to accept tasks 008 and 010; set their status | Tor | 19.11 |
| Answer keys for task 006, split between us | Both | to agree |
| Tasks 017 (reject cases) and 011 (replay cleans inputs) | to agree | to agree |
| Task 016 (kill switch) and task 012 (stress test, `eval-baseline` vs `main`) | to agree | to agree |
| Task 015 (model comparison) and task 009 (quote per bullet) if time allows | to agree | to agree |
