"""Check the summaries a run produced. Exit code 0 = every check passed, 1 = at least one failed.

    python -m harness.hamar_news.check           # checks out/summaries (real runs)
    python -m harness.hamar_news.check --mock    # checks out/mock/summaries

Everything here is decided by code, without a model:
  one_summary_per_article  state.json and the summary files agree, no duplicates or orphans
  header                   title, dates, link, language and model lines are present
  source_link              the link is the article's own hamar.kommune.no/lokaldemokrati URL
  dates_match_source       Published / Expires equal the dates in the saved source data
  summary_shape            the summary is non-empty; real runs have 3-6 flat '- ' bullets, none repeated
  no_contact_details       no e-mail addresses or phone numbers in the summary
  no_personal_names        no personal names in the title or the summary (heuristic, see names.py)
  no_invented_dates        every date in the summary also appears in the source text
  deadline_kept            a date after 'frist', 'innen' or 'senest' in the source is in the summary
  language                 the summary is in the requested language (English/Norwegian only)
  responsible_body         the summary does not say Hamar municipality acts when the source names another body
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .config import REPO_ROOT
from .extract import EMAIL, PHONE, Article, extract_article
from .fetch import LISTING_URL, is_article_url
from .names import find_person_names, scrub_person_names
from .summarise import NO_CONTENT

MONTHS = {
    # Norwegian (bokmål/nynorsk) and English month names -> month number.
    "januar": 1, "februar": 2, "mars": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7,
    "august": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "january": 1, "february": 2, "march": 3, "may": 5, "june": 6, "july": 7,
    "october": 10, "december": 12,
}
_MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))
NUMERIC_DATE = re.compile(r"\b(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4}|\d{2})\b")
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
DAY_MONTH = re.compile(rf"\b(\d{{1,2}})\.?\s+({_MONTH})\b(?:\s+(\d{{4}}))?", re.IGNORECASE)
MONTH_DAY = re.compile(rf"\b({_MONTH})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b,?(?:\s+(\d{{4}}))?", re.IGNORECASE)
NO_CONTENT_LINE = "_The model found no article content to summarise._"


def find_dates(text: str) -> set[tuple[int | None, int, int]]:
    """All dates in the text as (year or None, month, day)."""
    found: set[tuple[int | None, int, int]] = set()

    def add(y, m, d):
        if 1 <= m <= 12 and 1 <= d <= 31:
            found.add((y, m, d))

    for d, m, y in NUMERIC_DATE.findall(text):
        year = int(y) + 2000 if len(y) == 2 else int(y)
        add(year, int(m), int(d))
    for y, m, d in ISO_DATE.findall(text):
        add(int(y), int(m), int(d))
    for d, month, y in DAY_MONTH.findall(text):
        add(int(y) if y else None, MONTHS[month.lower()], int(d))
    for month, d, y in MONTH_DAY.findall(text):
        add(int(y) if y else None, MONTHS[month.lower()], int(d))
    return found


def date_in_source(date, source_dates) -> bool:
    y, m, d = date
    return any(m == sm and d == sd and (y is None or sy is None or y == sy)
               for sy, sm, sd in source_dates)


def parse_summary_file(md: str) -> tuple[dict[str, str], str]:
    """Return the '- **Field:** value' header lines and the text under '## Summary'."""
    head, _, summary = md.partition("\n## Summary\n")
    fields = dict(re.findall(r"^- \*\*(.+?):\*\* (.+)$", head, re.MULTILINE))
    title = head.splitlines()[0] if head else ""
    fields["_title"] = title[2:].strip() if title.startswith("# ") else ""
    return fields, summary.strip()


DEADLINE_CUE = re.compile(r"\b(?:s\u00f8knads)?frist(?:en)?\b|\binnen\b|\bsenest\b", re.IGNORECASE)


def source_deadlines(text: str) -> set[tuple[int | None, int, int]]:
    """Dates that follow a deadline word ("frist", "innen", "senest") within 50 characters."""
    found: set[tuple[int | None, int, int]] = set()
    for m in DEADLINE_CUE.finditer(text):
        found |= find_dates(text[m.start(): m.end() + 50])
    return found


# --- Language: a crude but transparent test on common function words -------------------------
_NO_WORDS = {"og", "er", "til", "som", "det", "på", "av", "ikke", "skal", "vil", "kan", "du", "fra",
             "med", "den", "har", "eller", "å", "seg", "oss", "vi", "også", "må", "blir", "ble",
             "etter", "før", "dette", "disse", "kommunen"}
_EN_WORDS = {"the", "and", "of", "to", "is", "are", "will", "can", "with", "on", "by", "from", "be",
             "this", "that", "which", "their", "has", "have", "must", "after", "before", "also", "or"}
_WORD = re.compile(r"[a-zæøåäöéü]+")


def language_problem(summary: str, language: str | None) -> str | None:
    """Flag a summary written in Norwegian when English was asked for, or the other way round.
    Other languages are not checked. Run 3 (03.11) produced a Norwegian summary for English."""
    if not language:
        return None
    words = _WORD.findall(summary.lower())
    no = sum(w in _NO_WORDS for w in words)
    en = sum(w in _EN_WORDS for w in words)
    wanted = language.strip().lower()
    if wanted.startswith("english") and no >= 3 and no > en:
        return f"language: the summary looks Norwegian ({no} vs {en} common words), but {language} was requested"
    if wanted.startswith(("norw", "nors", "bokm", "nyno")) and en >= 3 and en > no:
        return f"language: the summary looks English ({en} vs {no} common words), but {language} was requested"
    return None


# --- Responsible body: who is doing this? -----------------------------------------------------
# Run 3 named "Hamar municipality" as the actor in three articles where the county, a consultancy
# or Bufdir was responsible. The source usually names the actor with one of a few verbs.
_SOURCE_ACTOR = [
    re.compile(r"((?:[A-ZÆØÅ][\wæøåÆØÅ-]*[ \t]){0,2}[A-ZÆØÅ][\wæøåÆØÅ-]*(?:[ \t](?:AS|ASA|IKS|fylkeskommune|kommune))?)"
               r"[ \t]+(?:kunngjør|starter|varsler|lyser ut|inviterer)\b"),
    re.compile(r"administreres av ([A-ZÆØÅ][\wæøåÆØÅ-]+)"),
]
# Capitalised words at the start of a sentence that are not organisations.
_NOT_ACTORS = {"nå", "det", "vi", "kommunen", "planen", "arbeidet", "prosjektet", "her", "da", "snart",
               "hamar", "hamar kommune", "kommunestyret", "formannskapet", "dette", "hvem", "slik"}
_SUMMARY_HAMAR_ACTS = re.compile(
    r"\b(?:the\s+)?(?:municipality\s+of\s+hamar|hamar\s+municipality|hamar\s+kommune)\s+"
    r"(?:is|has|will|er|har|vil)\s+(?:now\s+|nå\s+)?"
    r"(?:start|launch|plan|hold|conduct|announc|introduc|begin|initiat|lanser|kunngj)\w*",
    re.IGNORECASE)


def source_actors(text: str) -> list[str]:
    """Bodies other than Hamar kommune that the source names as responsible."""
    found: list[str] = []
    for rule in _SOURCE_ACTOR:
        for m in rule.finditer(text):
            actor = m.group(1).strip()
            if actor.lower() not in _NOT_ACTORS and actor not in found:
                found.append(actor)
    return found


def _sentence_around(text: str, start: int, end: int) -> str:
    """The sentence (within one bullet line) that contains text[start:end]."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line = text[line_start: line_end if line_end != -1 else len(text)]
    offset = start - line_start
    begin = max(line.rfind(". ", 0, offset) + 2, 0) if line.rfind(". ", 0, offset) != -1 else 0
    stop = line.find(". ", offset)
    sentence = line[begin: stop + 1 if stop != -1 else len(line)]
    return sentence.lstrip("-*+ \t").strip()


def responsible_body_problem(summary: str, source_text: str) -> str | None:
    """Fail when the summary says Hamar municipality acts but the source names another body.
    Task 005: the message quotes the failing sentence and names the body, because in run 4 and
    the first eval run the model kept the same wrong sentence when told only what was wrong."""
    actors = source_actors(source_text)
    match = _SUMMARY_HAMAR_ACTS.search(summary)
    if not (actors and match):
        return None
    # The sentence is model output; never pass a personal name on to logs or the model.
    sentence = scrub_person_names(_sentence_around(summary, match.start(), match.end()))
    bodies = ", ".join(actors)
    return (f"responsible_body: the sentence \"{sentence}\" says Hamar municipality is doing it, "
            f"but the source names {bodies} as responsible. Rewrite that sentence so that "
            f"{actors[0]} is the one acting, as the source says.")


def validate_summary(summary: str, article, is_mock: bool, language: str | None = None) -> list[str]:
    """Problems with one summary, as 'check: detail' strings. Used by the check and by the
    pipeline, which gives the problems back to the model and asks it to try again."""
    problems: list[str] = []
    if not summary.strip():
        return ["summary_shape: summary is empty"]
    if summary.strip() in (NO_CONTENT_LINE, NO_CONTENT):
        return problems
    if not is_mock:
        lines = [l for l in summary.splitlines() if l.strip()]
        bullets = [l for l in lines if l.startswith(("- ", "* "))]
        if len(bullets) != len(lines):
            problems.append("summary_shape: summary has sub-points or lines that are not top-level bullet points")
        if not 3 <= len(bullets) <= 6:
            problems.append(f"summary_shape: {len(bullets)} bullet points, expected 3-6")
        texts = [b[2:].strip().lower() for b in bullets]
        if len(set(texts)) != len(texts):
            problems.append("summary_shape: the same bullet point appears more than once")
    if EMAIL.search(summary) or PHONE.search(summary):
        problems.append("no_contact_details: summary contains an e-mail address or phone number")
    names = find_person_names(summary)
    if names:
        # Report how many, never the names themselves: check.json must not hold personal data.
        problems.append(f"no_personal_names: {len(names)} personal name(s) in the summary")
    if not is_mock:
        for problem in (language_problem(summary, language), responsible_body_problem(summary, article.text)):
            if problem:
                problems.append(problem)

    source_dates = find_dates(article.text)
    summary_dates = find_dates(summary)
    for y, m, d in sorted(summary_dates, key=str):
        if not date_in_source((y, m, d), source_dates):
            problems.append(f"no_invented_dates: {d:02d}.{m:02d}.{y or '????'} is not in the source")
    if not is_mock:
        deadlines = source_deadlines(article.text)
        if deadlines and not any(date_in_source(d, summary_dates) for d in deadlines):
            shown = ", ".join(f"{d:02d}.{m:02d}" for _y, m, d in sorted(deadlines, key=lambda x: (x[1], x[2])))
            problems.append(f"deadline_kept: the deadline in the source ({shown}) is missing from the summary")
    return problems


@dataclass
class Result:
    slug: str
    failures: list[str] = field(default_factory=list)

    def fail(self, check: str, detail: str) -> None:
        self.failures.append(f"{check}: {detail}")


def load_source(slug: str, source_dir: Path, html_dir: Path | None = None) -> Article | None:
    """The cleaned article saved by the run. Runs from before 05.11 saved raw HTML instead; that
    is still read, so archived runs can be rescored."""
    path = source_dir / f"{slug}.json"
    if path.exists():
        return Article(**json.loads(path.read_text(encoding="utf-8")))
    if html_dir is not None and (html_dir / f"{slug}.html").exists():
        return extract_article((html_dir / f"{slug}.html").read_text(encoding="utf-8"), LISTING_URL + slug)
    return None


def check_article(slug: str, rec: dict, summaries_dir: Path, source_dir: Path,
                  html_dir: Path | None = None) -> Result:
    r = Result(slug)
    path = summaries_dir / rec["summary_file"]
    if not path.exists():
        r.fail("one_summary_per_article", f"{path.name} is listed in state.json but missing")
        return r
    fields, summary = parse_summary_file(path.read_text(encoding="utf-8"))

    for name in ("Published", "Original article", "Summary language", "Model"):
        if name not in fields:
            r.fail("header", f"missing '{name}' line")
    if not fields["_title"]:
        r.fail("header", "missing '# title' line")

    url = fields.get("Original article", "").strip("<>")
    if url != LISTING_URL + slug or not is_article_url(url):
        r.fail("source_link", f"link {url!r} is not {LISTING_URL + slug}")

    article = load_source(slug, source_dir, html_dir)
    if article is None:
        r.fail("dates_match_source", "saved source data is missing or not a single article")
    else:
        if fields.get("Published") != (article.published[:10] or "unknown"):
            r.fail("dates_match_source",
                   f"Published {fields.get('Published')} != source {article.published[:10]}")
        expires = fields.get("Expires / deadline")
        if (expires or "") != article.expires[:10]:
            r.fail("dates_match_source",
                   f"Expires {expires} != source {article.expires[:10] or 'none'}")

    is_mock = fields.get("Model") == "mock"
    if find_person_names(fields["_title"]):
        r.fail("no_personal_names", "the title names a person")
    if article is None:
        if not summary:
            r.fail("summary_shape", "summary is empty")
    else:
        for problem in validate_summary(summary, article, is_mock, fields.get("Summary language")):
            r.fail(*problem.split(": ", 1))
    return r


def check_run(out_dir: Path, mock: bool) -> tuple[list[Result], list[str]]:
    root = out_dir / "mock" if mock else out_dir
    summaries_dir, source_dir, html_dir = root / "summaries", out_dir / "source", out_dir / "html"
    state_path = root / "state.json"
    problems: list[str] = []
    if not state_path.exists():
        return [], [f"no state file at {state_path}; run the harness first"]
    articles = json.loads(state_path.read_text(encoding="utf-8")).get("articles", {})
    if not articles:
        problems.append("state.json lists no summarised articles")

    listed = {rec["summary_file"] for rec in articles.values()}
    on_disk = {p.name for p in summaries_dir.glob("*.md") if p.name != "INDEX.md"}
    for name in sorted(on_disk - listed):
        problems.append(f"one_summary_per_article: {name} is not listed in state.json")
    slugs_on_disk = [n.split("_", 1)[1] for n in on_disk if "_" in n]
    for slug in sorted({s for s in slugs_on_disk if slugs_on_disk.count(s) > 1}):
        problems.append(f"one_summary_per_article: more than one summary for {slug}")

    results = [check_article(slug, rec, summaries_dir, source_dir, html_dir)
               for slug, rec in sorted(articles.items())]
    return results, problems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m harness.hamar_news.check", description=__doc__.split("\n")[0])
    p.add_argument("--mock", action="store_true", help="check the mock run instead of the real one")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "out", help="output directory of the run")
    args = p.parse_args(argv)

    results, problems = check_run(args.out, args.mock)
    for r in results:
        print(("PASS " if not r.failures else "FAIL ") + r.slug)
        for f in r.failures:
            print("     " + f)
    for prob in problems:
        print("FAIL " + prob)
    passed = sum(not r.failures for r in results)
    ok = not problems and results and passed == len(results)
    print(f"\n{passed}/{len(results)} summaries passed" + ("" if not problems else f", {len(problems)} run-level problem(s)"))
    print("PASS" if ok else "FAIL")

    report = {"passed": passed, "total": len(results), "ok": bool(ok), "problems": problems,
              "failures": {r.slug: r.failures for r in results if r.failures}}
    root = args.out / "mock" if args.mock else args.out
    if root.exists():
        (root / "check.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
