"""Files on disk: saved HTML, stripped text, one Markdown summary per article, state and index."""

import json
import os
from datetime import datetime
from pathlib import Path

from .extract import Article
from .summarise import NO_CONTENT


class Store:
    def __init__(self, out_dir: Path, mock: bool):
        self.out_dir = Path(out_dir)
        # HTML and text are shared; summaries and "already done" state are kept apart for
        # mock runs so a mock run never stops a real run from summarising an article.
        self.root = self.out_dir / "mock" if mock else self.out_dir
        self.html_dir = self.out_dir / "html"
        self.text_dir = self.out_dir / "text"
        self.summaries_dir = self.root / "summaries"
        self.state_path = self.root / "state.json"
        for d in (self.html_dir, self.text_dir, self.summaries_dir):
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
        return slug in self.state["articles"] or slug in self.state.get("skipped", [])

    def mark_skipped(self, slug: str) -> None:
        """Remember pages that turned out not to be articles, so they are not refetched."""
        self.state.setdefault("skipped", []).append(slug)
        self._save_state()

    def save_html(self, slug: str, html: str) -> Path:
        path = self.html_dir / f"{slug}.html"
        path.write_text(html, encoding="utf-8")
        return path

    def save_text(self, article: Article) -> Path:
        path = self.text_dir / f"{article.slug}.txt"
        path.write_text(f"{article.url}\n\n{article.text}\n", encoding="utf-8")
        return path

    def write_summary(self, article: Article, summary: str, language: str, model: str,
                      truncated: bool) -> Path:
        date = article.published[:10] or datetime.now().strftime("%Y-%m-%d")
        path = self.summaries_dir / f"{date}_{article.slug}.md"
        if summary.strip() == NO_CONTENT:
            summary = "_The model found no article content to summarise._"

        lines = [
            f"# {article.title}",
            "",
            f"- **Published:** {article.published[:10] or 'unknown'}",
        ]
        if article.expires:
            lines.append(f"- **Expires / deadline:** {article.expires[:10]}")
        lines += [
            f"- **Original article:** <{article.url}>",
            f"- **Saved HTML:** [{article.slug}.html]({self._rel(self.html_dir / f'{article.slug}.html')})",
            f"- **Extracted text:** [{article.slug}.txt]({self._rel(self.text_dir / f'{article.slug}.txt')})",
            f"- **Summary language:** {language}",
            f"- **Model:** {model}",
            f"- **Summarised:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ]
        if truncated:
            lines.append("- **Note:** the article was too long and was truncated before summarising.")
        lines += ["", "## Summary", "", summary.strip(), ""]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def mark_done(self, article: Article, summary_path: Path, language: str, model: str) -> None:
        self.state["articles"][article.slug] = {
            "url": article.url,
            "title": article.title,
            "published": article.published[:10],
            "summary_file": summary_path.name,
            "language": language,
            "model": model,
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
            title = rec["title"].replace("|", "\\|")
            lines.append(f"| {rec['published']} | {title} | [summary]({rec['summary_file']}) "
                         f"| [hamar.kommune.no]({rec['url']}) | {rec['language']} |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _rel(self, target: Path) -> str:
        return Path(os.path.relpath(target, self.summaries_dir)).as_posix()
