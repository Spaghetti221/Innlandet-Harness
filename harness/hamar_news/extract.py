"""Strip an article page down to its raw text (title, lead, body) plus dates.

No personal data: the page author (og:article:author) is never read, and e-mail addresses,
phone numbers and personal names are replaced before the text is stored or sent to the model.
"""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from .fetch import slug_of
from .names import has_person_name, scrub_person_names

BLOCK_TAGS = ["p", "div", "li", "tr", "table", "ul", "ol", "section",
              "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "figcaption"]
DROP_TAGS = ["script", "style", "noscript", "button", "form", "iframe", "svg", "img"]

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?:\+47[\s-]?)?\b\d{2}[\s-]\d{2}[\s-]\d{2}[\s-]\d{2}\b|\+47[\s-]?\d{8}\b|\b\d{3}[\s-]\d{2}[\s-]\d{3}\b")


@dataclass
class Article:
    url: str
    slug: str
    title: str
    lead: str
    body: str
    published: str  # ISO timestamp or ""
    modified: str
    expires: str
    names_in_title: bool = False  # the article is about named people; the pipeline rejects it

    @property
    def text(self) -> str:
        """The stripped article text fed to the model."""
        parts = [self.title, self.lead, self.body]
        return "\n\n".join(p for p in parts if p)


def _meta(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find("meta", attrs={"property": prop})
    return (tag.get("content") or "").strip() if tag else ""


def is_article_page(soup: BeautifulSoup) -> bool:
    return _meta(soup, "og:type") == "article" and soup.select_one("article.single-article") is not None


def element_text(el: Tag) -> str:
    for tag in el.find_all(DROP_TAGS):
        tag.decompose()
    for br in el.find_all("br"):
        br.replace_with("\n")
    for li in el.find_all("li"):
        li.insert(0, "- ")
    for block in el.find_all(BLOCK_TAGS):
        block.append("\n")
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in el.get_text().splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def scrub_contact_details(text: str) -> str:
    text = EMAIL.sub("[e-post fjernet]", text)
    return PHONE.sub("[telefon fjernet]", text)


def scrub_personal_data(text: str) -> str:
    return scrub_person_names(scrub_contact_details(text))


def extract_article(html: str, url: str) -> Article | None:
    """Return the article, or None if the page is not a single article."""
    soup = BeautifulSoup(html, "html.parser")
    if not is_article_page(soup):
        return None
    root = soup.select_one("article.single-article")

    h1 = root.find("h1")
    title = element_text(h1) if h1 else _meta(soup, "og:title").removesuffix(" - Hamar kommune")
    lead_el = root.select_one('[itemprop="description"]')
    lead = element_text(lead_el) if lead_el else ""
    body = "\n\n".join(element_text(el) for el in root.select('[itemprop="articleBody"]'))

    return Article(
        url=url,
        slug=slug_of(url),
        title=scrub_personal_data(title),
        lead=scrub_personal_data(lead),
        body=scrub_personal_data(body),
        published=_meta(soup, "og:article:published_time"),
        modified=_meta(soup, "og:article:modified_time"),
        expires=_meta(soup, "og:article:expiration_time"),
        names_in_title=has_person_name(title),
    )
