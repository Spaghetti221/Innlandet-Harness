"""Find and remove personal names before text reaches the model, and check for them after.

Three heuristics, combined: (1) a common first name (data/first_names.txt) followed by one to
three capitalised words, e.g. "Kari Nordmann"; (2) capitalised words right after a phrase that
introduces a person ("rettes til", "kontaktperson er", "contact person"); (3) capitalised words
right before a contact detail ("Kari Nordmann, epost:"). They err on the side of removing too
much; a name with no list match, no cue and no contact detail can still be missed.
"""

import re
from pathlib import Path

NAMES_PATH = Path(__file__).parent / "data" / "first_names.txt"
PLACEHOLDER = "[navn fjernet]"


def _load_first_names() -> list[str]:
    lines = NAMES_PATH.read_text(encoding="utf-8").splitlines()
    return sorted({l.strip() for l in lines if l.strip() and not l.startswith("#")}, key=len, reverse=True)


_CAPITALISED = r"[A-ZÆØÅÄÖÉÜ][a-zæøåäöéüA-ZÆØÅ'’]+(?:-[A-ZÆØÅ][a-zæøåäöé]+)?"
_FULL_NAME = rf"{_CAPITALISED}(?:[ \t]+{_CAPITALISED}){{1,3}}"

# Rule 1: a common first name followed by one to three capitalised words.
PERSON_NAME = re.compile(
    rf"\b(?:{'|'.join(map(re.escape, _load_first_names()))})(?:[ \t]+{_CAPITALISED}){{1,3}}"
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
# Company and organisation suffixes: "Teknaconsult AS, e-post" is not a person.
_ORG_WORDS = {"AS", "ASA", "SA", "IKS", "KF", "BA", "Kommune", "Fylkeskommune"}


def _spans(text: str) -> list[tuple[int, int]]:
    spans = [m.span() for m in PERSON_NAME.finditer(text)]
    for rule in (NAME_AFTER_CUE, NAME_BEFORE_CONTACT):
        for m in rule.finditer(text):
            if not _ORG_WORDS.intersection(m.group("name").split()):
                spans.append(m.span("name"))
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def find_person_names(text: str) -> list[str]:
    return [text[a:b] for a, b in _spans(text)]


def has_person_name(text: str) -> bool:
    return bool(_spans(text))


def scrub_person_names(text: str) -> str:
    for a, b in reversed(_spans(text)):
        text = text[:a] + PLACEHOLDER + text[b:]
    return text
