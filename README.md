# vocab

A CLI tool that looks up words and displays definitions, frequency data, etymology, synonyms/antonyms, and related words. Features a interactive mode with autocomplete and autocorrect.

## Install

```bash
pip install -e .
```

## Usage

```bash
vocab                          # interactive shell
vocab hello world              # look up words directly
vocab -b hello                 # brief definition only
vocab -j hello                 # JSON output
vocab -f wordlist.txt          # read words from file
echo "hello" | vocab           # read from stdin
vocab -s def freq syn hello    # show only specific sections
vocab --offline hello          # skip API calls, use WordNet/wordfreq only
vocab --no-cache hello         # bypass disk cache
vocab --no-color hello         # disable colors
vocab --cache-dir /tmp hello   # custom cache directory
```

## Interactive Shell

Run `vocab` with no arguments to enter the interactive shell.

```
vocab> hello
vocab> /help
```

Commands:
- `/help` — show help
- `/clear` — clear the screen
- `/clear-cache` — remove all cached lookups
- `/clear-history` — clear search history
- `/file <path>` — look up words from a file
- `/exit`, `/quit` — exit the shell

Features:
- Fish-style grey ghost text autosuggestions from history
- Tab completion from WordNet (~150k words) and slash commands
- Autocorrect with confirmation for misspelled words
- Automatic lemmatization (e.g. "added" → "add", "mice" → "mouse")

## Data Sources

- **WordNet** (offline) — definitions, synonyms, antonyms, brief glosses, lemmatization
- **wordfreq** (offline) — zipf score, per-million frequency, usage label
- **Free Dictionary API** — definitions, phonetics, synonyms, antonyms
- **Wiktionary** — etymology, related/derived terms

## License

MIT
