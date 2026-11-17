"""Task 010 check: a summary that still fails after its last attempt is withheld, not shown.

    python eval/check_withheld.py --out out/run6
    python eval/check_withheld.py --out out/eval --mock-bad-run      # every summary withheld
    python eval/check_withheld.py --out out/run6 --export app/src/data/<export>.json

PASS when, for every article in state.json:
- passed_check false  -> the Summary section has no bullet points, it contains the line
  "No summary:", and the header has no "read before use"
- passed_check true   -> the Summary section has at least one bullet point
With --export: the exported JSON gives no bullets for any withheld article.
With --mock-bad-run: every article must be withheld (run with --mock-bad, task 010).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from _run import articles, report, roots, summary

MARKER = "No summary:"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-bad-run", action="store_true")
    ap.add_argument("--export", type=Path)
    a = ap.parse_args()
    _, root = roots(a.out, a.mock)

    errors, withheld = [], set()
    for slug, rec in articles(root).items():
        fields, bullets, body = summary(root, rec)
        if rec.get("passed_check", False):
            if not bullets:
                errors.append(f"{slug}: passed but has no bullet points")
            if a.mock_bad_run:
                errors.append(f"{slug}: passed under --mock-bad; the checks let a bad summary through")
            continue
        withheld.add(slug)
        if bullets:
            errors.append(f"{slug}: failed its checks but still shows {len(bullets)} bullet point(s)")
        if MARKER not in body:
            errors.append(f"{slug}: failed its checks but has no '{MARKER}' line")
        if "read before use" in fields.get("Check", ""):
            errors.append(f"{slug}: still marked 'read before use' instead of withheld")

    if a.export:
        items = json.loads(a.export.read_text(encoding="utf-8"))
        items = items.get("items", items) if isinstance(items, dict) else items
        for item in items:
            if item.get("slug") in withheld:
                for lang, s in (item.get("summaries") or {}).items():
                    if s.get("bullets"):
                        errors.append(f"{item['slug']}: withheld, but the export has {lang} bullets")

    print(f"withheld: {len(withheld)}")
    return report(errors)


if __name__ == "__main__":
    sys.exit(main())
