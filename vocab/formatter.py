"""Rich-based colored terminal output."""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from vocab.core import WordResult


def format_result(result: WordResult, brief: bool = False, console: Console | None = None) -> None:
    """Print a formatted word result to the terminal."""
    if console is None:
        console = Console()

    # Word header + phonetic
    header = Text(result.word, style="bold white")
    if result.phonetic:
        header.append(f"  {result.phonetic}", style="dim")
    console.print(header)

    # Brief definition
    brief_def = result.brief_definition()
    if brief_def:
        console.print(Text(brief_def, style="italic cyan"))

    if brief:
        return

    # Full definitions by part of speech
    if result.definitions:
        console.print()
        for pos, defs in result.definitions.items():
            console.print(Text(pos, style="bold yellow"))
            for i, d in enumerate(defs[:5], 1):  # cap at 5 per POS
                console.print(f"  {i}. {d}")

    # Frequency
    if result.frequency:
        console.print()
        f = result.frequency
        console.print(Text("Frequency", style="bold yellow"))
        console.print(f"  {f['per_million']}/million  ·  zipf {f['zipf']}  ·  {f['label']}")

    # Etymology
    if result.etymology_text:
        console.print()
        console.print(Text("Etymology", style="bold yellow"))
        for section in result.etymology_text.split("\n\n"):
            console.print(f"  {section}")

    # Root words
    if result.root_words:
        console.print()
        console.print(Text("Root words", style="bold yellow"))
        console.print(f"  {' → '.join(result.root_words)}")

    # Related/derived words
    if result.related_words:
        console.print()
        console.print(Text("Related words", style="bold yellow"))
        console.print(f"  {', '.join(result.related_words)}")

    # Synonyms
    if result.synonyms:
        console.print()
        console.print(Text("Synonyms", style="bold yellow"))
        syn_text = Text(f"  {', '.join(result.synonyms[:15])}", style="green")
        console.print(syn_text)

    # Antonyms
    if result.antonyms:
        console.print()
        console.print(Text("Antonyms", style="bold yellow"))
        ant_text = Text(f"  {', '.join(result.antonyms[:15])}", style="red")
        console.print(ant_text)

    # Base word (lemmatized form)
    if result.base_word and result.base_result:
        console.print()
        console.print(Text(f"Base form: {result.base_word}", style="bold magenta"))
        format_result(result.base_result, brief=brief, console=console)
        return

    console.print()
