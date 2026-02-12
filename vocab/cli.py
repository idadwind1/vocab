"""CLI argument parsing and mode routing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console

from vocab.cache import DiskCache
from vocab.core import lookup_word
from vocab.formatter import format_result
from vocab.sources.wordnet import ensure_data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vocab",
        description="Look up words: definitions, frequency, etymology, synonyms, and more.",
    )
    p.add_argument("words", nargs="*", help="Words to look up")
    p.add_argument("-f", "--file", type=Path, help="Read words from file")
    p.add_argument("-b", "--brief", action="store_true", help="Brief definition only")
    p.add_argument("-j", "--json", action="store_true", dest="json_output", help="JSON output")
    p.add_argument(
        "-s", "--sections", nargs="+",
        choices=["def", "freq", "syn", "ety"],
        help="Show only specific sections",
    )
    p.add_argument("--offline", action="store_true", help="Skip API calls")
    p.add_argument("--no-cache", action="store_true", help="Bypass disk cache")
    p.add_argument("--no-color", action="store_true", help="Disable colors")
    p.add_argument("--cache-dir", type=Path, help="Custom cache directory")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Ensure WordNet data is available
    ensure_data()

    console = Console(no_color=args.no_color)
    cache = None if args.no_cache else DiskCache(args.cache_dir or DiskCache().cache_dir)

    # Collect words from all sources
    words: list[str] = list(args.words)

    if args.file:
        try:
            words.extend(args.file.read_text().split())
        except OSError as e:
            console.print(f"[red]Error reading file:[/red] {e}")
            sys.exit(1)

    if not sys.stdin.isatty() and not words:
        words.extend(sys.stdin.read().split())

    # No words provided → interactive mode
    if not words:
        from vocab.interactive import run_interactive
        run_interactive(
            offline=args.offline,
            no_cache=args.no_cache,
            no_color=args.no_color,
            cache_dir=args.cache_dir,
            brief=args.brief,
            sections=args.sections,
        )
        return

    # Direct lookup mode
    for word in words:
        word = word.strip().lower()
        if not word:
            continue
        result = lookup_word(
            word,
            offline=args.offline,
            cache=cache if not args.no_cache else None,
            no_cache=args.no_cache,
            sections=args.sections,
        )
        if args.json_output:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            format_result(result, brief=args.brief, console=console)
