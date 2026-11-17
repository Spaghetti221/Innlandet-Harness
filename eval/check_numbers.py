"""Task 008 check: every number in a summary occurs in its source, and the deadline and
case number in the header come from the source.

    python eval/check_numbers.py --out out/eval2
    python eval/check_numbers.py --out out/eval --mock

Numbers: amounts, counts, case numbers, postcodes, years. Numeric dates (18.11.2026,
2026-11-18) are skipped: check 7 in harness/hamar_news/check.py already parses dates.
"1 200", "1.200" and "1,200" are read as 1200 on both sides.

Header (task 008): if a "Case number (from source)" field is present, its digits must occur
in the source. The header deadline is a date, so the harness tests cover it, not this check.
Withheld summaries (task 010) have no bullets, so they pass trivially.

Known gap: a number that is in the source but attached to the wrong thing passes
(03.11/05.11: "Hamarlånet loan (450 million kroner)"; the 450 million is the start loan).
"""
import argparse
import re
import sys

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from _run import articles, norm, report, roots, source_text, summary

DATE = re.compile(r"\b\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
GROUPED = re.compile(r"\b\d{1,3}(?:[ ., ]\d{3})+\b")
DIGITS = re.compile(r"\d+")


def numbers(text: str, skip_dates: bool) -> set[str]:
    text = norm(text)
    if skip_dates:
        text = DATE.sub(" ", text)
    found = {re.sub(r"\D", "", m) for m in GROUPED.findall(text)}
    found |= set(DIGITS.findall(text))
    return {n.lstrip("0") or "0" for n in found}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    out_dir, root = roots(a.out, a.mock)

    errors = []
    for slug, rec in articles(root).items():
        fields, bullets, _ = summary(root, rec)
        src = source_text(out_dir, slug)
        if not src:
            errors.append(f"{slug}: no extracted text in {out_dir / 'text'}")
            continue
        in_source = numbers(src, skip_dates=False)
        for n in sorted(numbers(" ".join(bullets), skip_dates=True) - in_source, key=int):
            errors.append(f"{slug}: the summary has the number {n}, which is not in the source")
        case_no = fields.get("Case number (from source)")
        if case_no and case_no.lower() not in {"none", "not stated"}:
            if numbers(case_no, skip_dates=False) - in_source:
                errors.append(f"{slug}: header case number {case_no!r} is not in the source")
    return report(errors)


if __name__ == "__main__":
    sys.exit(main())
