"""WordNet-based autocomplete + difflib autocorrect."""

from __future__ import annotations

import difflib

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


COMMANDS = ["/clear", "/clear-cache", "/clear-history", "/exit", "/file", "/help", "/quit"]


class WordCompleter(Completer):
    """Tab-completion from WordNet lemma list + slash commands."""

    def __init__(self) -> None:
        self._words: list[str] | None = None

    def _load(self) -> list[str]:
        if self._words is None:
            from vocab.sources.wordnet import all_lemmas
            self._words = sorted(all_lemmas())
        return self._words

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.strip().lower()
        if not text:
            return

        # Slash commands
        if text.startswith("/"):
            for cmd in COMMANDS:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
            return

        if len(text) < 2:
            return
        words = self._load()
        # Binary search for prefix range
        import bisect
        lo = bisect.bisect_left(words, text)
        count = 0
        for i in range(lo, len(words)):
            if not words[i].startswith(text):
                break
            yield Completion(words[i], start_position=-len(text))
            count += 1
            if count >= 20:
                break


def suggest_correction(word: str, word_set: set[str] | None = None) -> list[str]:
    """Suggest close matches for a misspelled word."""
    if word_set is None:
        from vocab.sources.wordnet import all_lemmas
        word_set = all_lemmas()
    # Filter candidates by length similarity for performance
    wlen = len(word)
    candidates = [w for w in word_set if abs(len(w) - wlen) <= 2]
    return difflib.get_close_matches(word, candidates, n=3, cutoff=0.7)
