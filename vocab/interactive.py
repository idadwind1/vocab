"""Fish-style interactive shell with autosuggestions and tab completion."""

from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console

from vocab.cache import DiskCache
from vocab.completer import WordCompleter, suggest_correction
from vocab.core import lookup_word
from vocab.formatter import format_result
from vocab.sources.wordnet import all_lemmas

HISTORY_DIR = Path.home() / ".local" / "share" / "vocab"
HISTORY_FILE = HISTORY_DIR / "history"


def run_interactive(
    offline: bool = False,
    no_cache: bool = False,
    no_color: bool = False,
    cache_dir: Path | None = None,
    brief: bool = False,
    sections: list[str] | None = None,
) -> None:
    """Run the interactive REPL."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    console = Console(no_color=no_color)
    cache = DiskCache(cache_dir) if cache_dir else (None if no_cache else DiskCache())
    completer = WordCompleter()
    lemmas: set[str] | None = None

    session: PromptSession = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
    )

    console.print("[bold]vocab[/bold] interactive shell  (type /help for commands, Ctrl+D to exit)")

    while True:
        try:
            text = session.prompt("vocab> ").strip()
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

        if not text:
            continue

        # Slash commands
        if text in ("/exit", "/quit", "exit", "quit"):
            break
        if text == "/clear":
            console.clear()
            continue
        if text == "/clear-cache":
            if cache:
                count = cache.clear()
                console.print(f"[dim]Cleared {count} cached entries.[/dim]")
            else:
                console.print("[dim]Cache is disabled.[/dim]")
            continue
        if text == "/clear-history":
            try:
                HISTORY_FILE.unlink(missing_ok=True)
                session.history = FileHistory(str(HISTORY_FILE))
                console.print("[dim]History cleared.[/dim]")
            except OSError as e:
                console.print(f"[red]Error clearing history:[/red] {e}")
            continue
        if text == "/help":
            console.print(
                "[bold]Commands:[/bold]\n"
                "  /help          Show this help\n"
                "  /clear         Clear the screen\n"
                "  /clear-cache   Remove all cached lookups\n"
                "  /clear-history Clear search history\n"
                "  /file <path>   Look up words from a file\n"
                "  /exit          Exit the shell\n"
                "  /quit          Exit the shell\n"
                "\nType any word to look it up."
            )
            continue
        if text.startswith("/file"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Usage:[/red] /file <path>")
                continue
            filepath = Path(parts[1]).expanduser()
            try:
                file_words = filepath.read_text().split()
            except OSError as e:
                console.print(f"[red]Error reading file:[/red] {e}")
                continue
            if not file_words:
                console.print("[dim]File is empty.[/dim]")
                continue
            console.print(f"[dim]Looking up {len(file_words)} word(s) from {filepath.name}[/dim]")
            for fw in file_words:
                fw = fw.strip().lower()
                if not fw:
                    continue
                r = lookup_word(
                    fw,
                    offline=offline,
                    cache=cache if not no_cache else None,
                    no_cache=no_cache,
                    sections=sections,
                )
                format_result(r, brief=brief, console=console)
            continue

        word = text.split()[0].lower()

        # Autocorrect check
        if lemmas is None:
            lemmas = all_lemmas()
        if word not in lemmas:
            suggestions = suggest_correction(word, lemmas)
            if suggestions:
                options = "  ".join(
                    f"[bold][{i}][/bold] {s}" for i, s in enumerate(suggestions, 1)
                )
                console.print(f"[dim]Not found. Did you mean:[/dim]  {options}")
                try:
                    choice = session.prompt("Enter number to accept, or press Enter to skip: ").strip()
                except (KeyboardInterrupt, EOFError):
                    continue
                if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                    word = suggestions[int(choice) - 1]
                elif choice == "":
                    continue
                else:
                    console.print("[dim]Skipped.[/dim]")
                    continue

        result = lookup_word(
            word,
            offline=offline,
            cache=cache if not no_cache else None,
            no_cache=no_cache,
            sections=sections,
        )
        format_result(result, brief=brief, console=console)
