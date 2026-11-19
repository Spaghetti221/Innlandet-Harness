"""Summarisers: a real one that calls a local Ollama server, and a mock for testing."""

import re
from pathlib import Path

import requests

NO_CONTENT = "NO_CONTENT"
# Conservative estimate for Norwegian (~3.5-4 with the Llama 3 tokenizer; not yet measured for Qwen).
CHARS_PER_TOKEN = 3

# The system prompt is a context file, kept next to the code so it can be reviewed and versioned.
PROMPT_PATH = Path(__file__).parent / "prompts" / "summarise_system.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
# The English glossary of planning terms (tasks 007/013) was removed on the qwen3.5-9b branch:
# the larger model is expected to translate without help, and the checks no longer enforce it.


TITLE_PROMPT = (PROMPT_PATH.parent / "translate_title_system.md").read_text(encoding="utf-8")
NORWEGIAN_PREFIXES = ("norw", "nors", "bokm", "nyno")


def system_prompt(language: str) -> str:
    return SYSTEM_PROMPT.format(language=language, no_content=NO_CONTENT)


def needs_title_translation(language: str) -> bool:
    """The titles are Norwegian already; every other language gets a translated title."""
    return not language.strip().lower().startswith(NORWEGIAN_PREFIXES)


def title_messages(title: str, language: str, previous: str | None = None,
                   problems: list[str] | None = None) -> list[dict]:
    """A separate, short conversation for the title (task 014): its own check and retries, so a
    bad title never forces the summary to be rewritten, and the other way round."""
    system = TITLE_PROMPT.format(language=language)
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": f"<title>{title}</title>"}]
    if previous is not None and problems:
        listed = "\n".join(f"- {p}" for p in problems)
        messages += [{"role": "assistant", "content": previous},
                     {"role": "user", "content": f"Your title broke these rules:\n{listed}\n\n"
                                                 "Write the translated title again, on one line."}]
    return messages


RETRY_INSTRUCTION = (
    "Your summary broke these rules:\n{problems}\n\n"
    "Write the summary again. Use one flat list of 3 to 6 lines that each start with \"- \", "
    "with no sub-points and no indentation. Merge related points into one line if needed. "
    "Keep every deadline from the article, and follow all the other rules."
)


FORMAT_HINT = (
    "Write the summary in {language}. Use one flat list of 3 to 6 lines that each start with "
    "\"- \". If the article contains a list, summarise that list in one line, for example "
    "\"- The changes include A, B and C.\"; never end a line with \":\" followed by sub-points."
)
ACTOR_HINT = (
    "The article names {actor} as responsible. Write that {actor} is doing it, "
    "not Hamar municipality."
)


def build_hints(language: str, actors: list[str] | None = None) -> list[str]:
    """Reminders placed after the article, closest to where the model starts writing. The 3B
    model broke format, language and actor rules on the first attempt in the 17.11 run.
    The language is stated as the task, not as translation help (no glossary)."""
    hints = [FORMAT_HINT.format(language=language)]
    if actors:
        hints.append(ACTOR_HINT.format(actor=actors[0]))
    return hints


def build_messages(text: str, language: str, previous: str | None = None,
                   problems: list[str] | None = None,
                   hints: list[str] | None = None) -> list[dict]:
    """The conversation sent to the model. Hints (from code, not from the article) follow the
    article. On a retry, the previous answer and the problems the code check found are added,
    so the model can correct itself."""
    user = f"<article>\n{text}\n</article>"
    if hints:
        user += "\n\n" + "\n".join(hints)
    messages = [
        {"role": "system", "content": system_prompt(language)},
        {"role": "user", "content": user},
    ]
    if previous is not None and problems:
        listed = "\n".join(f"- {p}" for p in problems)
        messages += [
            {"role": "assistant", "content": previous},
            {"role": "user", "content": RETRY_INSTRUCTION.format(problems=listed)},
        ]
    return messages


def truncate(text: str, max_tokens: int) -> tuple[str, bool]:
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text, False
    cut = text[:max_chars]
    # Prefer to cut at a paragraph or sentence boundary.
    for sep in ("\n\n", ". "):
        idx = cut.rfind(sep)
        if idx > max_chars * 0.8:
            cut = cut[: idx + len(sep)]
            break
    return cut.rstrip(), True


THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


class OllamaSummariser:
    def __init__(self, url: str, model: str, num_ctx: int, timeout: float = 600.0,
                 think: bool | None = None):
        self.url = url.rstrip("/")
        self.name = model
        self.num_ctx = num_ctx
        self.timeout = timeout
        self.think = think

    def _chat(self, messages: list[dict]) -> str:
        body = {
            "model": self.name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": self.num_ctx},
        }
        if self.think is not None:
            body["think"] = self.think
        resp = requests.post(f"{self.url}/api/chat", json=body, timeout=self.timeout)
        resp.raise_for_status()
        # Older Ollama versions leave a thinking model's reasoning in the content.
        return THINK_BLOCK.sub("", resp.json()["message"]["content"]).strip()

    def summarise(self, text: str, language: str, previous: str | None = None,
                  problems: list[str] | None = None, hints: list[str] | None = None) -> str:
        return self._chat(build_messages(text, language, previous, problems, hints))

    def translate_title(self, title: str, language: str, previous: str | None = None,
                        problems: list[str] | None = None) -> str:
        return self._chat(title_messages(title, language, previous, problems))


class MockSummariser:
    """Deterministic stand-in for the model: no network, no model needed."""

    name = "mock"

    def summarise(self, text: str, language: str, previous: str | None = None,
                  problems: list[str] | None = None, hints: list[str] | None = None) -> str:
        if not text.strip():
            return NO_CONTENT
        # Keep paragraphs apart: joining a title to the next line ("... Veltvegen Teknaconsult
        # starter") makes two capitalised words that the name check reads as a person.
        sentences = [s for para in text.split("\n\n")
                     for s in re.split(r"(?<=[.!?])\s+", " ".join(para.split())) if s]
        bullets = "\n".join(f"- {s}" for s in sentences[:3])
        return f"- [MOCK] Summary would be written in {language}. First sentences of the source:\n{bullets}"

    def translate_title(self, title: str, language: str, previous: str | None = None,
                        problems: list[str] | None = None) -> str:
        return f"{title} ({language}, mock)"

class MockBadSummariser:
    """A fake model that always breaks the checks: Norwegian text (whatever language was asked
    for) with a date that is in no source. Used to test that failing summaries are withheld.
    Its name is not "mock", so the full checks apply to it."""

    name = "mock-bad"

    def summarise(self, text: str, language: str, previous: str | None = None,
                  problems: list[str] | None = None, hints: list[str] | None = None) -> str:
        return ("- Kommunen ber om innspill innen 29.12.2031.\n"
                "- Saken skal behandles i kommunestyret.\n"
                "- Les mer på kommunens nettside.")
