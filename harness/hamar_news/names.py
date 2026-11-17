"""Find and remove personal names before text reaches the model, and check for them after.

Three heuristics, combined: (1) a common first name (data/first_names.txt) followed by one to
three capitalised words, e.g. "Kari Nordmann"; (2) capitalised words right after a phrase that
introduces a person ("rettes til", "kontaktperson er", "contact person"); (3) capitalised words
right before a contact detail ("Kari Nordmann, epost:"). They err on the side of removing too
much; a name with no list match, no cue and no contact detail can still be missed.

A fourth layer (17.11) is a statistical named-entity recogniser (spaCy, run locally): it finds
person names from the sentence itself, without a list or a cue. Its spans are added to the
heuristics' (union). Real runs require it (require_ner); without it, the heuristics run alone.
"""

import logging
import re
from functools import cache
from pathlib import Path

log = logging.getLogger(__name__)

NAMES_PATH = Path(__file__).parent / "data" / "first_names.txt"
PLACEHOLDER = "[name removed]"  # static English since 18.11 (was "[navn fjernet]")
# spaCy models: Norwegian Bokmål (trained on NorNE) for source text, English for summaries.
NER_MODELS = {"nb": "nb_core_news_md", "en": "en_core_web_sm"}
NER_PERSON_LABELS = {"PER", "PERSON"}


def _load_first_names() -> list[str]:
    lines = NAMES_PATH.read_text(encoding="utf-8").splitlines()
    return sorted({l.strip() for l in lines if l.strip() and not l.startswith("#")}, key=len, reverse=True)


_CAPITALISED = r"[A-ZÆØÅÄÖÉÜ][a-zæøåäöéüA-ZÆØÅ'’]+(?:-[A-ZÆØÅ][a-zæøåäöé]+)?"
_FULL_NAME = rf"{_CAPITALISED}(?:[ \t]+{_CAPITALISED}){{1,3}}"

FIRST_NAMES = _load_first_names()
_FIRST_NAME_SET = set(FIRST_NAMES)
# Rule 1: a common first name (also as the first half of a double name, "Ola-Petter") followed
# by one to three capitalised words. Live run 17.11 leaked a hyphenated first name.
PERSON_NAME = re.compile(
    rf"\b(?:{'|'.join(map(re.escape, FIRST_NAMES))})(?:-[A-ZÆØÅ][a-zæøåäöé]+)?(?:[ \t]+{_CAPITALISED}){{1,3}}"
)
# Rule 2: two to four capitalised words right after a phrase that introduces a person, so names
# are found even when the first name is not in the list (run 3 missed "Janne ...").
_CUE = (r"rettes til|kontaktperson(?:en|er)?(?: for [a-zæøå ]+)?(?: er)?:?|saksbehandler(?:en)?(?: er)?:?"
        r"|prosjektleder(?:en)?(?: er)?:?|contact person(?: is)?:?|case officer(?: is)?:?"
        r"|project manager(?: is)?:?|directed to|addressed to")
NAME_AFTER_CUE = re.compile(rf"(?i:\b(?:{_CUE}))[ \t]+(?P<name>{_FULL_NAME})")
# Rule 3: two to four capitalised words followed directly by a contact detail ("Kari Nordmann, epost:").
NAME_BEFORE_CONTACT = re.compile(
    rf"(?P<name>\b{_FULL_NAME})(?=,?[ \t]*(?i:e-?post|epost|e-mail|mob\.?|mobil|tlf\.?|telefon|phone)\b)"
)
# Rule 4: two to four capitalised words joined to a name already removed ("[name removed] og
# Kari Nordmann"): people are often named in pairs. Works on the second pass of scrub_person_names.
_P = re.escape(PLACEHOLDER)
NAME_NEXT_TO_REMOVED = re.compile(
    rf"{_P}(?:,|[ \t]+og|[ \t]+and)[ \t]+(?P<name>{_FULL_NAME})"
    rf"|(?P<name2>\b{_FULL_NAME})(?:,|[ \t]+og|[ \t]+and)[ \t]+{_P}"
)
# Company and organisation suffixes: "Teknaconsult AS, e-post" is not a person.
_ORG_WORDS = {"AS", "ASA", "SA", "IKS", "KF", "BA", "Kommune", "Kommunen", "Kommunene", "Fylkeskommune", "Fylkeskommunen"}


@cache
def _ner_model(lang: str):
    """The spaCy pipeline for 'nb' or 'en', loaded once; None if spaCy or the model is missing
    (or, as on one Windows machine, its native libraries are blocked)."""
    try:
        import spacy
        return spacy.load(NER_MODELS[lang], disable=["parser", "lemmatizer"])
    except Exception as exc:  # ImportError, OSError (model not downloaded), blocked DLLs
        log.debug("NER model for %r unavailable: %s", lang, exc)
        return None


def ner_available(lang: str = "nb") -> bool:
    return _ner_model(lang) is not None


def require_ner() -> None:
    """Fail closed: a real run must not send text to the model with only the heuristics."""
    missing = [m for lang, m in NER_MODELS.items() if not ner_available(lang)]
    if missing:
        raise RuntimeError(
            "named-entity model(s) not available: " + ", ".join(missing) + ". Install with "
            + " and ".join(f"'python -m spacy download {m}'" for m in missing)
            + ", or use --mock.")


_NOT_A_NAME_CHARS = re.compile(r"[\d/@\[\]]|\.\w")  # numbers, URLs, addresses, placeholders


def accept_ner_span(text: str, start: int, end: int) -> bool:
    """Decide whether a span the NER model labelled as a person is treated as a name.

    The 17.11 runs showed what the model gets wrong on these notices: single words that are
    places or projects (Børstad, Stange, Jernbanebrygga, Hamarlånet), lowercase words ("avløp",
    "per post"), URLs and street addresses ("Luramyrveien 25A"). Real names there were either
    two or more capitalised words, or a single known first name ("Kari og ...")."""
    span = text[start:end]
    if "\n" in span:  # a name never runs over two lines (bullet points, headings)
        return False
    words = span.split()
    if _NOT_A_NAME_CHARS.search(span) or _ORG_WORDS.intersection(words):
        return False
    if not all(w[0].isupper() for w in words):
        return False
    if len(words) == 1:
        # A lone word only if it is a known first name, and not "Per 1. januar" (per = each).
        followed_by_number = re.match(r"[ \t]*\d", text[end:end + 3]) is not None
        return span in _FIRST_NAME_SET and not followed_by_number
    return True


def _ner_spans(text: str, lang: str) -> list[tuple[int, int]]:
    nlp = _ner_model(lang)
    if nlp is None:
        return []
    return [(e.start_char, e.end_char) for e in nlp(text).ents
            if e.label_ in NER_PERSON_LABELS and accept_ner_span(text, e.start_char, e.end_char)]


def _spans(text: str, lang: str = "nb") -> list[tuple[int, int]]:
    spans = [m.span() for m in PERSON_NAME.finditer(text)]
    for rule in (NAME_AFTER_CUE, NAME_BEFORE_CONTACT):
        for m in rule.finditer(text):
            if not _ORG_WORDS.intersection(m.group("name").split()):
                spans.append(m.span("name"))
    for m in NAME_NEXT_TO_REMOVED.finditer(text):
        group = "name" if m.group("name") else "name2"
        if not _ORG_WORDS.intersection(m.group(group).split()):
            spans.append(m.span(group))
    spans += _ner_spans(text, lang)
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def ner_lang(language: str | None) -> str:
    """'en' for an English summary, else 'nb' (source text and Norwegian summaries)."""
    return "en" if (language or "").strip().lower().startswith("english") else "nb"


def find_person_names(text: str, lang: str = "nb") -> list[str]:
    return [text[a:b] for a, b in _spans(text, lang)]


def has_person_name(text: str, lang: str = "nb") -> bool:
    return bool(_spans(text, lang))


def scrub_person_names(text: str, lang: str = "nb", max_passes: int = 3) -> str:
    """Replace names, then look again: the NER model reads context, and on 17.11 it labelled
    the second of two prize winners as an organisation until the first name was replaced.
    Rule 4 also needs a placeholder from an earlier pass. Stops when a pass finds nothing."""
    for _ in range(max_passes):
        spans = _spans(text, lang)
        if not spans:
            break
        for a, b in reversed(spans):
            text = text[:a] + PLACEHOLDER + text[b:]
    return text
