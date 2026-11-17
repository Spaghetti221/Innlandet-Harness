"""Task 009 check: every bullet of a passed summary is backed by a quote from the source.

    python eval/check_evidence.py --out out/run6

For each article with passed_check true, <root>/evidence/<slug>.json must look like
    {"slug": "...", "bullets": [{"text": "<the bullet as in the summary>",
                                 "quote": "<Norwegian sentence copied from the source>"}]}
and:
- it has one entry per summary bullet, in the same order, with the same text
- every quote is at least 20 characters and occurs word for word in the extracted text
  (after quote, dash, whitespace and case normalisation; no fuzzy matching)

Known gap: the quote exists, but the English bullet can still say something the quote
does not. That needs a human or an LLM judge (Level 2).
"""
import argparse
import json
import sys

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from _run import articles, norm, report, roots, source_text, summary

MIN_QUOTE = 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    out_dir, root = roots(a.out, a.mock)

    errors, checked = [], 0
    for slug, rec in articles(root).items():
        if not rec.get("passed_check", False):
            continue
        _, bullets, _ = summary(root, rec)
        path = root / "evidence" / f"{slug}.json"
        if not path.exists():
            errors.append(f"{slug}: passed, but there is no {path}")
            continue
        entries = json.loads(path.read_text(encoding="utf-8")).get("bullets", [])
        if len(entries) != len(bullets):
            errors.append(f"{slug}: {len(bullets)} bullets but {len(entries)} evidence entries")
            continue
        src = norm(source_text(out_dir, slug))
        for i, (bullet, entry) in enumerate(zip(bullets, entries), start=1):
            checked += 1
            if norm(entry.get("text", "")) != norm(bullet):
                errors.append(f"{slug}: bullet {i} differs from its evidence entry")
            quote = norm(entry.get("quote", ""))
            if len(quote) < MIN_QUOTE:
                errors.append(f"{slug}: bullet {i} has no quote of at least {MIN_QUOTE} characters")
            elif quote not in src:
                errors.append(f"{slug}: bullet {i} quote is not in the source: {entry.get('quote')!r}")
    if checked == 0:
        errors.append("no passed summaries with bullets: nothing was checked")
    print(f"bullets checked: {checked}")
    return report(errors)


if __name__ == "__main__":
    sys.exit(main())
