"""ety library wrapper for root word chains. Gracefully skipped if unavailable."""


def lookup(word: str) -> list[str]:
    """Return list of root/origin words, or empty list if ety unavailable."""
    try:
        import ety
        origins = ety.origins(word, recursive=True)
        return [str(o) for o in origins] if origins else []
    except Exception:
        return []
