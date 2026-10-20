# Plan 001: Add a todo item from the CLI

<!-- EXAMPLE: the agent writes this from spec.md, and you review it before any code. -->

## Approach
A single Python CLI entry point with an `add` subcommand. Storage is a JSON file
holding a list of `{id, text, done}` objects. The next ID is max(existing) + 1.

## Changes
- `todo/cli.py`: argument parsing, `add` subcommand
- `todo/store.py`: load/save the data file, create it if missing
- `tests/test_add.py`: one test per acceptance criterion

## Requirement coverage
| Req | How it's met |
|-----|--------------|
| R1 | `add` appends an item and saves |
| R2 | ID = max(ids) + 1, starting at 1 |
| R3 | Strip text, exit 1 with error if empty |
| R4 | `store.load()` returns [] and creates the file if missing |
| R5 | Print `Added #<id>` |

## Risks / alternatives considered
- SQLite: rejected. The brief requires a human-readable file.
