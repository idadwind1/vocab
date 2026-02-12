"""WordResult dataclass and lookup orchestrator."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from vocab.sources import dictionary_api, wiktionary, wordnet, etymology, frequency
from vocab.cache import DiskCache


@dataclass
class WordResult:
    word: str
    phonetic: str = ""
    definitions: dict[str, list[str]] = field(default_factory=dict)
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)
    frequency: dict = field(default_factory=dict)
    etymology_text: str = ""
    root_words: list[str] = field(default_factory=list)
    related_words: list[str] = field(default_factory=list)
    base_word: str = ""
    base_result: WordResult | None = None

    brief_def: str = ""

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        if self.base_result:
            d["base_result"] = self.base_result.to_dict()
        else:
            d["base_result"] = None
        return d

    @staticmethod
    def from_dict(d: dict) -> WordResult:
        br = d.pop("base_result", None)
        result = WordResult(**d)
        if br:
            result.base_result = WordResult.from_dict(br)
        return result

    def brief_definition(self) -> str:
        """Return the WordNet brief gloss, or fall back to truncated first definition."""
        if self.brief_def:
            return self.brief_def
        for defs in self.definitions.values():
            if defs:
                return _truncate(defs[0])
        return ""


def _truncate(text: str, max_words: int = 6) -> str:
    """Truncate to 3-6 words, stopping at natural boundaries."""
    words = text.split()
    if len(words) <= max_words:
        return text
    stop_words = {"and", "or", "but", "which", "that", "who"}
    for i in range(3, min(max_words + 1, len(words))):
        if words[i].lower() in stop_words or words[i - 1].endswith(","):
            return " ".join(words[:i])
    result = " ".join(words[:max_words])
    if not result.endswith("."):
        result += "..."
    return result


def lookup_word(
    word: str,
    offline: bool = False,
    cache: DiskCache | None = None,
    no_cache: bool = False,
    sections: list[str] | None = None,
) -> WordResult:
    """Orchestrate lookups across all sources."""
    # Check cache
    if cache and not no_cache:
        cached = cache.get(word)
        if cached:
            return WordResult.from_dict(cached)

    result = WordResult(word=word)
    want = set(sections) if sections else None

    # Frequency (always offline, fast)
    if not want or "freq" in want:
        result.frequency = frequency.lookup(word)

    # Definitions: try API first, fall back to WordNet
    api_data = None
    if not offline and (not want or want & {"def", "syn"}):
        api_data = dictionary_api.lookup(word)

    wn_data = None
    if not api_data or offline:
        wn_data = wordnet.lookup(word)

    # Brief definition from WordNet (always, since it's a different phrasing)
    if not wn_data:
        wn_data = wordnet.lookup(word)
    if wn_data:
        result.brief_def = wn_data.get("brief", "")

    if api_data and (not want or "def" in want):
        result.phonetic = api_data.get("phonetic", "")
        result.definitions = api_data.get("definitions", {})
    elif wn_data and (not want or "def" in want):
        result.definitions = wn_data.get("definitions", {})

    # Synonyms/antonyms: merge API + WordNet
    if not want or "syn" in want:
        syns: set[str] = set()
        ants: set[str] = set()
        if api_data:
            syns.update(api_data.get("synonyms", []))
            ants.update(api_data.get("antonyms", []))
        if wn_data or (not api_data and not offline):
            if not wn_data:
                wn_data = wordnet.lookup(word)
            if wn_data:
                syns.update(wn_data.get("synonyms", []))
                ants.update(wn_data.get("antonyms", []))
        result.synonyms = sorted(syns)
        result.antonyms = sorted(ants)

    # Etymology from Wiktionary
    if not offline and (not want or "ety" in want):
        wiki_data = wiktionary.lookup(word)
        if wiki_data:
            result.etymology_text = wiki_data.get("etymology", "")
            result.related_words = wiki_data.get("related", [])

    # Root words from ety library
    if not want or "ety" in want:
        result.root_words = etymology.lookup(word)

    # Lemmatization: if this is an inflected form, also look up the base word
    base = wordnet.lemmatize(word)
    if base and base != word:
        result.base_word = base
        result.base_result = lookup_word(
            base, offline=offline, cache=cache, no_cache=no_cache, sections=sections,
        )

    # Cache result
    if cache and not no_cache:
        cache.set(word, result.to_dict())

    return result
