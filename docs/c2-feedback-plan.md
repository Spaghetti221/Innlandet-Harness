# C2 feedback: plan for the exam version

## The feedback (Compulsory 2)

Strengths: identified the weaknesses of the Lokaldemokrati page; connected the notification
function with the subsequent action.

To improve:
1. "Factual accuracy is low; for public announcements, an incorrect summary can be worse than
   having no announcement at all."
2. "Name removal relies on a list of names and simple patterns."

## Measured before any change (17.11)

| Check (new, in `eval/`) | Run | Result | What it shows |
|---|---|---|---|
| `check_withheld.py` | `out/eval2` | FAIL | HØP failed its checks after 3 attempts and is still shown ("read before use") and exported |
| `check_evidence.py` | `out/eval2` | FAIL | no bullet is tied to a source sentence |
| `check_numbers.py` | `out/eval2` | PASS | every number is in the source, yet HØP gives the 450 million to the wrong loan: numbers alone are not enough |
| `check_perturbations.py` | `--replay fixtures/hamar_news/perturbed --mock` | FAIL | 0 of 3 planted names removed, the name-in-title case not rejected |

Why the names leak: `run_replay` never scrubs again and trusts the stored `names_in_title`;
and run through `names.py` directly, the heuristics still catch 0 of the 3 planted names and
not the names in the title. "Kontaktperson i Hamar kommune er rådgiver Testa Fiktivsen" is
missed because "i Hamar kommune" sits between the cue and the name.

## Tasks, in order

| # | Task | Feedback | Size |
|---|---|---|---|
| 006 | Answer keys and one-command Level 2 score (already planned). Tag `eval-baseline` when done | 1 (measure first) | M |
| 010 | Withhold a summary that still fails, instead of "read before use" | 1 | S |
| 008 | Numbers checked against the source; deadline and case number in the header from code | 1 | S |
| 011 | Name removal with NER, also in replay | 2 | M |
| 009 | A source quote for every bullet | 1 | L |
| 012 | Stress test: 5 runs each on `eval-baseline` and `main` | both, exam §3.3 | M |

If time runs short, 009 is the one to report as future work rather than half-build: 008, 010
and 011 each close a measured failure on their own.

## Two kinds of check, on purpose

- `harness/hamar_news/check.py` runs inside the pipeline so a failing summary can go back to
  the model with feedback. The agent may edit it.
- `eval/check_*.py` judge a finished run. They import nothing from `harness/`, and
  `Edit(/eval/**)` is denied, so a change to the harness cannot change what passes.
  Commit each before its task and see it fail (red first).

## Rules for every task

- Gold keys (task 006) and perturbations are written by us, not by the agent.
- One branch and one PR per task; the person who wrote the task reviews the diff.
- One prompt-log line per task where we corrected or rejected the agent.
- In the white paper: feedback → change → measured effect, and the gaps that remain
  (a quote can exist while the English bullet still says something else).
