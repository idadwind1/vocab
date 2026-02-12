"""Free Dictionary API (dictionaryapi.dev) source."""

import requests

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"


def lookup(word: str, timeout: float = 5.0) -> dict | None:
    """Return parsed dictionary data or None on failure."""
    try:
        resp = requests.get(API_URL.format(word=word), timeout=timeout)
        if resp.status_code != 200:
            return None
        entries = resp.json()
        if not isinstance(entries, list) or not entries:
            return None
        return _parse(entries)
    except (requests.RequestException, ValueError, KeyError):
        return None


def _parse(entries: list[dict]) -> dict:
    phonetic = ""
    definitions: dict[str, list[str]] = {}
    synonyms: set[str] = set()
    antonyms: set[str] = set()

    for entry in entries:
        # phonetic
        if not phonetic:
            phonetic = entry.get("phonetic", "")
            if not phonetic:
                for p in entry.get("phonetics", []):
                    if p.get("text"):
                        phonetic = p["text"]
                        break

        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "unknown")
            for d in meaning.get("definitions", []):
                text = d.get("definition", "")
                if text:
                    definitions.setdefault(pos, []).append(text)
            synonyms.update(meaning.get("synonyms", []))
            antonyms.update(meaning.get("antonyms", []))
            for d in meaning.get("definitions", []):
                synonyms.update(d.get("synonyms", []))
                antonyms.update(d.get("antonyms", []))

    return {
        "phonetic": phonetic,
        "definitions": definitions,
        "synonyms": sorted(synonyms),
        "antonyms": sorted(antonyms),
    }
