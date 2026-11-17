"""Shared helpers for the eval/ checks: read one run directory the way the harness writes it.

Kept in eval/ on purpose: the checks must not import harness code, so a change to the
harness cannot quietly change what the checks accept.

Layout (harness/hamar_news/store.py):
  <out>/source/<slug>.json, <out>/text/<slug>.txt               shared
  <root>/state.json, <root>/summaries/, <root>/attempts/<slug>/   root = <out> or <out>/mock
  <root>/evidence/<slug>.json                                     added by task 009
"""
import json
import re
import unicodedata
from pathlib import Path

FIELD = re.compile(r"^- \*\*(.+?):\*\* ?(.*)$", re.MULTILINE)
BULLET = re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE)


def norm(s: str) -> str:
    """Compare text after Unicode, quote, dash, whitespace and case normalisation only."""
    s = unicodedata.normalize("NFC", s or "")
    s = s.translate(str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"', "’": "'",
                                   "–": "-", "—": "-", " ": " "}))
    return re.sub(r"\s+", " ", s).strip().casefold()


def roots(out: str, mock: bool) -> tuple[Path, Path]:
    out_dir = Path(out)
    return out_dir, (out_dir / "mock" if mock else out_dir)


def articles(root: Path) -> dict:
    state = root / "state.json"
    if not state.exists():
        raise SystemExit(f"FAIL: no {state}; run the harness first")
    return json.loads(state.read_text(encoding="utf-8")).get("articles", {})


def summary(root: Path, rec: dict) -> tuple[dict, list[str], str]:
    """Header fields, bullet texts and the raw Summary section of one summary file."""
    md = (root / "summaries" / rec["summary_file"]).read_text(encoding="utf-8")
    head, _, body = md.partition("## Summary")
    fields = {k: v.strip() for k, v in FIELD.findall(head)}
    bullets = [b.strip() for b in BULLET.findall(body)]
    return fields, bullets, body


def source_text(out_dir: Path, slug: str) -> str:
    path = out_dir / "text" / f"{slug}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def report(errors: list[str]) -> int:
    for e in errors:
        print("FAIL:", e)
    print("FAIL" if errors else "PASS")
    return 1 if errors else 0
