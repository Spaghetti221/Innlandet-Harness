"""Files on disk: cleaned source data, stripped text, one Markdown summary per article, every
model attempt, state and index.

The raw HTML is never stored: it contains names and contact boxes. Only the cleaned article
(names, e-mail addresses and phone numbers replaced) and its dates are kept, which is all the
check needs.
"""

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .check import case_numbers_from_source
from .export import deadline_from_source
from .extract import Article
from .fetch import anonymous_slug, digest
from .summarise import NO_CONTENT

# Shown instead of a summary that still fails its checks after the last attempt (task 010):
# a wrong summary can be worse than none. The model's text stays in attempts/ only.
WITHHELD_LINE = ("_No summary: the automatic summary did not pass the checks after {attempts} attempts. "
                 "Read the original article._")


class Store:
    def __init__(self, out_dir: Path, mock: bool):
        self.out_dir = Path(out_dir)
        # Source data and text are shared; summaries, attempts and "already done" state are kept
        # apart for mock runs so a mock run never stops a real run from summarising an article.
        self.root = self.out_dir / "mock" if mock else self.out_dir
        self.source_dir = self.out_dir / "source"
        self.text_dir = self.out_dir / "text"
        self.summaries_dir = self.root / "summaries"
        self.attempts_dir = self.root / "attempts"
        self.state_path = self.root / "state.json"
        for d in (self.source_dir, self.text_dir, self.summaries_dir, self.attempts_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"articles": {}}

    def _save_state(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.state_path)

    def is_done(self, slug: str) -> bool:
        # An article whose title names people is stored under a hashed slug (anonymous_slug).
        # "rejected" holds hashes from runs before 17.11, when such articles were refused.
        return (slug in self.state["articles"] or slug in self.state.get("skipped", [])
                or anonymous_slug(slug) in self.state["articles"]
                or digest(slug) in self.state.get("rejected", []))

    digest = staticmethod(digest)

    def mark_skipped(self, slug: str) -> None:
        """Remember pages that turned out not to be articles, so they are not refetched."""
        self.state.setdefault("skipped", []).append(slug)
        self._save_state()

    def save_source(self, article: Article) -> Path:
        """The cleaned article and its dates, as JSON. Replaces the raw HTML stored before 05.11."""
        path = self.source_dir / f"{article.slug}.json"
        path.write_text(json.dumps(asdict(article), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def save_attempt(self, slug: str, attempt: int, summary: str, problems: list[str],
                     kind: str = "summary") -> Path:
        """Every model answer is kept, with the problems the check found, so a retry that makes a
        summary worse can be seen afterwards. Title attempts (task 014) go to title-attempt-N.md."""
        folder = self.attempts_dir / slug
        folder.mkdir(parents=True, exist_ok=True)
        prefix = "title-attempt" if kind == "title" else "attempt"
        path = folder / f"{prefix}-{attempt}.md"
        found = "\n".join(f"- {p}" for p in problems) or "- none (passed)"
        heading = f"Title attempt {attempt}" if kind == "title" else f"Attempt {attempt}"
        path.write_text(f"# {heading}\n\n## Problems found\n\n{found}\n\n## Model answer\n\n"
                        f"{summary.strip()}\n", encoding="utf-8")
        return path

    def save_text(self, article: Article) -> Path:
        path = self.text_dir / f"{article.slug}.txt"
        path.write_text(f"{article.url}\n\n{article.text}\n", encoding="utf-8")
        return path

    def write_summary(self, article: Article, summary: str, language: str, model: str,
                      truncated: bool, attempts: int = 1, problems: list[str] | None = None,
                      title_translated: str | None = None) -> Path:
        # The file name keeps the slug: the check, state.json and the export use it as the key.
        date = article.published[:10] or datetime.now().strftime("%Y-%m-%d")
        path = self.summaries_dir / f"{date}_{article.slug}.md"
        if problems:
            summary = WITHHELD_LINE.format(attempts=attempts)
        elif summary.strip() == NO_CONTENT:
            summary = "_The model found no article content to summarise._"

        lines = [f"# {title_translated or article.title}", ""]
        if title_translated:
            # Readers match the summary with the Norwegian page by its original title.
            lines.append(f"- **Original title:** {article.title}")
        lines.append(f"- **Published:** {article.published[:10] or 'unknown'}")
        if article.expires:
            lines.append(f"- **Expires / deadline:** {article.expires[:10]}")
        # Task 008: key facts taken from the source by code, never by the model.
        deadline = deadline_from_source(article.text, article.published[:10])
        case_numbers = case_numbers_from_source(article.text)
        lines.append(f"- **Deadline (from source):** {deadline or 'not stated'}")
        lines.append(f"- **Case number (from source):** {', '.join(case_numbers) or 'not stated'}")
        lines += [
            f"- **Original article:** <{article.url}>",
            f"- **Saved source:** [{article.slug}.json]({self._rel(self.source_dir / f'{article.slug}.json')})",
            f"- **Extracted text:** [{article.slug}.txt]({self._rel(self.text_dir / f'{article.slug}.txt')})",
            f"- **Summary language:** {language}",
            f"- **Model:** {model}",
            f"- **Summarised:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ]
        lines.append(f"- **Attempts:** {attempts}")
        if problems:
            lines.append(f"- **Check:** withheld after {attempts} attempt(s)")
        if truncated:
            lines.append("- **Note:** the article was too long and was truncated before summarising.")
        lines += ["", "## Summary", "", summary.strip(), ""]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def mark_done(self, article: Article, summary_path: Path, language: str, model: str,
                  attempts: int = 1, problems: list[str] | None = None,
                  title_translated: str | None = None) -> None:
        self.state["articles"][article.slug] = {
            "url": article.url,
            "title": article.title,
            "title_translated": title_translated,
            "published": article.published[:10],
            "summary_file": summary_path.name,
            "language": language,
            "model": model,
            "attempts": attempts,
            "passed_check": not problems,
            "summarised_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._save_state()

    def write_index(self) -> Path:
        path = self.summaries_dir / "INDEX.md"
        rows = sorted(self.state["articles"].items(),
                      key=lambda kv: (kv[1]["published"], kv[0]), reverse=True)
        lines = [
            "# Hamar kommune – lokaldemokrati summaries",
            "",
            "| Published | Title | Summary | Original | Language |",
            "|---|---|---|---|---|",
        ]
        for _slug, rec in rows:
            title = (rec.get("title_translated") or rec["title"]).replace("|", "\\|")
            label = "summary" if rec.get("passed_check", True) else "withheld"
            lines.append(f"| {rec['published']} | {title} | [{label}]({rec['summary_file']}) "
                         f"| [hamar.kommune.no]({rec['url']}) | {rec['language']} |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _rel(self, target: Path) -> str:
        return Path(os.path.relpath(target, self.summaries_dir)).as_posix()
