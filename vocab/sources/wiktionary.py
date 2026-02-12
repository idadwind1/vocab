"""Wiktionary scraper for etymology and related/derived words."""

import requests
from bs4 import BeautifulSoup, Tag

WIKTIONARY_URL = "https://en.wiktionary.org/wiki/{word}"
HEADERS = {"User-Agent": "vocab-cli/0.1 (https://github.com/vocab-cli; educational tool)"}


def lookup(word: str, timeout: float = 5.0) -> dict | None:
    """Return etymology text and related/derived words, or None."""
    try:
        resp = requests.get(
            WIKTIONARY_URL.format(word=word),
            headers=HEADERS,
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        return {
            "etymology": _extract_etymology(soup),
            "related": _extract_related(soup),
        }
    except (requests.RequestException, Exception):
        return None


def _find_section_div(soup: BeautifulSoup, name: str) -> Tag | None:
    """Find the first mw-heading div that contains a heading matching name."""
    for div in soup.find_all("div", class_="mw-heading"):
        heading = div.find(["h2", "h3", "h4"])
        if heading and name in heading.get_text():
            return div
    return None


def _find_all_section_divs(soup: BeautifulSoup, name: str) -> list[Tag]:
    """Find all mw-heading divs that contain a heading matching name."""
    results = []
    for div in soup.find_all("div", class_="mw-heading"):
        heading = div.find(["h2", "h3", "h4"])
        if heading and name in heading.get_text():
            results.append(div)
    return results


def _content_after(div: Tag) -> list[Tag]:
    """Collect sibling elements after a mw-heading div until the next mw-heading."""
    elements = []
    for sib in div.find_next_siblings():
        if not isinstance(sib, Tag):
            continue
        if "mw-heading" in (sib.get("class") or []):
            break
        elements.append(sib)
    return elements


def _extract_etymology(soup: BeautifulSoup) -> str:
    """Collect text from all Etymology sections, filtering noise."""
    divs = _find_all_section_divs(soup, "Etymology")
    if not divs:
        return ""
    sections = []
    for div in divs:
        parts = []
        for el in _content_after(div):
            if el.name == "p":
                text = el.get_text(" ", strip=True)
                # Skip Wiktionary boilerplate and trivial entries
                if "etymology is missing" in text.lower():
                    continue
                if "Please add to it" in text:
                    continue
                parts.append(text)
        if parts:
            combined = " ".join(parts)
            # Skip very short trivial sections like "From English hello."
            if len(combined) > 30:
                sections.append(combined)
    return "\n\n".join(sections) if sections else ""


def _extract_related(soup: BeautifulSoup) -> list[str]:
    """Extract related/derived terms from Wiktionary."""
    words: list[str] = []
    for section_name in ("Related terms", "Derived terms"):
        div = _find_section_div(soup, section_name)
        if not div:
            continue
        for el in _content_after(div):
            for li in el.find_all("li"):
                a = li.find("a")
                if a:
                    text = a.get_text(strip=True)
                else:
                    text = li.get_text(strip=True)
                if text and len(text) < 50 and text not in words:
                    words.append(text)
    return words[:20]
