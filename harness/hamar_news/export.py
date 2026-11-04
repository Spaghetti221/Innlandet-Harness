"""Export summaries as JSON for the Expo reader app in app/.

Reads state.json and the Markdown summaries of one or more runs (one per summary language)
and writes one JSON file the app bundles. Only the summaries, the dates and the article
link are exported; no source text or HTML. Articles whose title names people, and summaries
in which a personal name is found, are left out.
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from .check import find_dates, parse_summary_file
from .config import REPO_ROOT
from .names import has_person_name

BULLET = re.compile(r"^(\s*)[-*+]\s+(.+)$")
# Broader than check.DEADLINE_CUE: also compounds such as "høringsfristen" and "Uttalefrist".
DEADLINE_CUE = re.compile(r"\w*frist\w*|\binnen\b|\bsenest\b", re.IGNORECASE)

# First match wins, so "Oppstart av planarbeid – si din mening" counts as a hearing.
KINDS = [
    ("hearing", re.compile(r"høring|offentlig ettersyn|si din mening|innspill", re.IGNORECASE)),
    ("grant", re.compile(r"tilskudd|søk om|stipend", re.IGNORECASE)),
    ("plan", re.compile(r"oppstart|planarbeid|reguleringsplan|kommunedelplan", re.IGNORECASE)),
    ("decision", re.compile(r"vedtatt|godkjent|vedtak", re.IGNORECASE)),
]


def kind_of(title: str) -> str:
    return next((kind for kind, pattern in KINDS if pattern.search(title)), "info")


def language_code(language: str) -> str:
    return "no" if language.lower().startswith(("norw", "nors", "bokm")) else "en"


def parse_bullets(summary: str) -> list[dict]:
    """Top-level bullets, each with the indented sub-bullets the model sometimes adds.
    A heading-like bullet ("Residents can:") with nothing under it is dropped."""
    bullets: list[dict] = []
    for line in summary.splitlines():
        m = BULLET.match(line)
        if not m:
            continue
        if m.group(1) and bullets:
            bullets[-1]["children"].append(m.group(2).strip())
        else:
            bullets.append({"text": m.group(2).strip(), "children": []})
    return [b for b in bullets if b["children"] or not b["text"].endswith(":")]


def deadline_from_source(text: str, published: str) -> str | None:
    """The earliest date after a deadline word ("frist", "innen", "senest") on or after publishing."""
    try:
        start = date.fromisoformat(published)
    except ValueError:
        return None
    dates: set[tuple[int | None, int, int]] = set()
    for cue in DEADLINE_CUE.finditer(text):
        dates |= find_dates(text[cue.start(): cue.end() + 50])
    found = []
    for y, m, d in dates:
        try:
            day = date(y or start.year, m, d)
            if y is None and day < start:
                day = date(start.year + 1, m, d)
        except ValueError:
            continue
        if day >= start:
            found.append(day)
    return min(found).isoformat() if found else None


def export_runs(run_dirs: list[Path], mock: bool) -> list[dict]:
    items: dict[str, dict] = {}
    found_state = False
    for run_dir in run_dirs:
        root = run_dir / "mock" if mock else run_dir
        state_path = root / "state.json"
        if not state_path.exists():
            continue
        found_state = True
        articles = json.loads(state_path.read_text(encoding="utf-8")).get("articles", {})
        for slug, rec in articles.items():
            path = root / "summaries" / rec["summary_file"]
            if not path.exists() or has_person_name(rec["title"]):
                continue
            fields, summary = parse_summary_file(path.read_text(encoding="utf-8"))
            if has_person_name(summary):
                # A name the scrubbing missed reached the summary (run 3, 03.11): never export it.
                continue
            title = fields.get("_title") or rec["title"]
            item = items.get(slug)
            if item is None:
                text_path = run_dir / "text" / f"{slug}.txt"
                text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
                item = items[slug] = {
                    "slug": slug,
                    "title": title,
                    "kind": kind_of(title),
                    "published": rec["published"],
                    "expires": fields.get("Expires / deadline"),
                    "deadline": deadline_from_source(text, rec["published"]),
                    "url": rec["url"],
                    "summaries": {},
                }
            item["summaries"][language_code(rec["language"])] = {
                "model": rec["model"],
                "bullets": parse_bullets(summary),
                "passedCheck": rec.get("passed_check", True),
                "truncated": "Note" in fields,
            }
    if not found_state:
        raise FileNotFoundError(f"no state file in {', '.join(map(str, run_dirs))}; run the harness first")
    return sorted(items.values(), key=lambda it: (it["published"], it["slug"]), reverse=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m harness.hamar_news.export", description=__doc__.split("\n")[0])
    p.add_argument("--mock", action="store_true", help="export the mock runs instead of the real ones")
    p.add_argument("--run", type=Path, action="append", dest="runs",
                   help="output directory of a run; repeat for each language (default: out and out/no)")
    p.add_argument("--dest", type=Path, default=REPO_ROOT / "app" / "src" / "data" / "summaries.json",
                   help="where to write the JSON")
    args = p.parse_args(argv)
    runs = args.runs or [REPO_ROOT / "out", REPO_ROOT / "out" / "no"]

    try:
        items = export_runs(runs, args.mock)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    args.dest.parent.mkdir(parents=True, exist_ok=True)
    args.dest.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    langs = sorted({lang for it in items for lang in it["summaries"]})
    print(f"wrote {len(items)} articles ({', '.join(langs)}) to {args.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
