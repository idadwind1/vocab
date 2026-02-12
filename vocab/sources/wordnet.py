"""NLTK WordNet source for offline definitions, synonyms, and antonyms."""

from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer

_lemmatizer = WordNetLemmatizer()


def ensure_data() -> None:
    """Download WordNet data if not present."""
    import nltk
    try:
        wn.synsets("test")
    except LookupError:
        nltk.download("wordnet", quiet=True)


def lookup(word: str) -> dict | None:
    """Return definitions, synonyms, and antonyms from WordNet."""
    synsets = wn.synsets(word)
    if not synsets:
        return None

    definitions: dict[str, list[str]] = {}
    synonyms: set[str] = set()
    antonyms: set[str] = set()

    pos_map = {"n": "noun", "v": "verb", "a": "adjective", "s": "adjective", "r": "adverb"}

    for ss in synsets:
        pos = pos_map.get(ss.pos(), ss.pos())
        defn = ss.definition()
        if defn:
            definitions.setdefault(pos, []).append(defn)
        for lemma in ss.lemmas():
            name = lemma.name().replace("_", " ")
            if name.lower() != word.lower():
                synonyms.add(name)
            for ant in lemma.antonyms():
                antonyms.add(ant.name().replace("_", " "))

    return {
        "definitions": definitions,
        "synonyms": sorted(synonyms),
        "antonyms": sorted(antonyms),
        "brief": _shortest_gloss(synsets),
    }


def _shortest_gloss(synsets) -> str:
    """Pick one short gloss per distinct POS, joined with ' / '."""
    pos_map = {"n": "noun", "v": "verb", "a": "adj", "s": "adj", "r": "adv"}
    seen_pos: dict[str, str] = {}
    for ss in synsets:
        pos = pos_map.get(ss.pos(), ss.pos())
        if pos in seen_pos:
            continue
        g = ss.definition()
        if g and len(g) >= 3:
            clean = g.split(";")[0].strip()
            # Truncate long glosses to ~6 words
            words = clean.split()
            if len(words) > 6:
                stop = {"and", "or", "but", "which", "that", "who"}
                cut = 6
                for i in range(3, min(7, len(words))):
                    if words[i].lower() in stop or words[i - 1].endswith(","):
                        cut = i
                        break
                clean = " ".join(words[:cut]) + "..."
            seen_pos[pos] = clean
    if not seen_pos:
        return ""
    return " / ".join(seen_pos.values())


def all_lemmas() -> set[str]:
    """Return all WordNet lemma names for autocomplete."""
    ensure_data()
    return {l.replace("_", " ") for l in wn.all_lemma_names()}


def lemmatize(word: str) -> str | None:
    """Return the base/lemma form if the word is inflected, or None if already base."""
    bases: set[str] = set()
    for pos in ("n", "v", "a", "r"):
        lemma = _lemmatizer.lemmatize(word, pos)
        if lemma != word:
            bases.add(lemma)
    if not bases:
        return None
    # Prefer the base form that has the most synsets (most likely intended meaning)
    return max(bases, key=lambda b: len(wn.synsets(b)))
