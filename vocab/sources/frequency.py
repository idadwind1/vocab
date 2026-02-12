"""Word frequency data via wordfreq library."""

from wordfreq import zipf_frequency, word_frequency


def lookup(word: str, lang: str = "en") -> dict:
    """Return frequency metrics for a word."""
    zipf = zipf_frequency(word, lang)
    freq = word_frequency(word, lang)
    per_million = freq * 1e6

    if zipf >= 6:
        label = "very common"
    elif zipf >= 5:
        label = "common"
    elif zipf >= 4:
        label = "familiar"
    elif zipf >= 3:
        label = "uncommon"
    elif zipf >= 2:
        label = "rare"
    else:
        label = "very rare"

    return {
        "zipf": round(zipf, 2),
        "per_million": round(per_million, 2),
        "percentage": round(freq * 100, 6),
        "label": label,
    }
