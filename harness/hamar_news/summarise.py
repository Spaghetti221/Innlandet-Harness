"""Summarisers: a real one that calls a local Ollama server, and a mock for testing."""

import re
from pathlib import Path

import requests

NO_CONTENT = "NO_CONTENT"
# Conservative estimate for Norwegian with the Llama 3 tokenizer (real ratio is ~3.5-4).
CHARS_PER_TOKEN = 3

# The system prompt is a context file, kept next to the code so it can be reviewed and versioned.
PROMPT_PATH = Path(__file__).parent / "prompts" / "summarise_system.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
# Fixed translations of planning terms, added only for English summaries (the 3B model
# translated "pumpestasjon" as "power station" in the first real run).
GLOSSARY_EN = (PROMPT_PATH.parent / "glossary_en.md").read_text(encoding="utf-8")


def system_prompt(language: str) -> str:
    prompt = SYSTEM_PROMPT.format(language=language, no_content=NO_CONTENT)
    if language.strip().lower().startswith("english"):
        prompt += "\n" + GLOSSARY_EN
    return prompt


RETRY_INSTRUCTION = (
    "Your summary broke these rules:\n{problems}\n\n"
    "Write the summary again. Use one flat list of 3 to 6 lines that each start with \"- \", "
    "with no sub-points and no indentation. Merge related points into one line if needed. "
    "Keep every deadline from the article, and follow all the other rules."
)


def build_messages(text: str, language: str, previous: str | None = None,
                   problems: list[str] | None = None) -> list[dict]:
    """The conversation sent to the model. On a retry, the previous answer and the problems the
    code check found are added, so the model can correct itself."""
    messages = [
        {"role": "system", "content": system_prompt(language)},
        {"role": "user", "content": f"<article>\n{text}\n</article>"},
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


class OllamaSummariser:
    def __init__(self, url: str, model: str, num_ctx: int, timeout: float = 600.0):
        self.url = url.rstrip("/")
        self.name = model
        self.num_ctx = num_ctx
        self.timeout = timeout

    def summarise(self, text: str, language: str, previous: str | None = None,
                  problems: list[str] | None = None) -> str:
        resp = requests.post(
            f"{self.url}/api/chat",
            json={
                "model": self.name,
                "messages": build_messages(text, language, previous, problems),
                "stream": False,
                "options": {"temperature": 0.2, "num_ctx": self.num_ctx},
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()


class MockSummariser:
    """Deterministic stand-in for the model: no network, no model needed."""

    name = "mock"

    def summarise(self, text: str, language: str, previous: str | None = None,
                  problems: list[str] | None = None) -> str:
        if not text.strip():
            return NO_CONTENT
        flat = " ".join(text.split())
        sentences = re.split(r"(?<=[.!?])\s+", flat)
        bullets = "\n".join(f"- {s}" for s in sentences[:3])
        return f"- [MOCK] Summary would be written in {language}. First sentences of the source:\n{bullets}"
