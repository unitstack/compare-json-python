# compare-json

[![PyPI](https://img.shields.io/pypi/v/compare-json-py)](https://pypi.org/project/compare-json-py/)

Python port of [`compare-json`](https://github.com/unitstack/compare-json) — **structured JSON comparison**: find what changed between two JSON values, with control over how keys, values, and arrays are matched.

> Online playground: **[comparejson.com](https://comparejson.com)**

## Why

Most JSON diff tools either output unstructured text or hide the parts that matter (where a key was added, whether a type changed, whether two arrays differ in order or in content). `compare-json` returns a structured list of differences — every entry carries a path, the side it belongs to (`base` / `contrast` / `both`), and the kind of change (`added`, `deleted`, `typeChanged`, `valueChanged`) — so you can render, filter, or program against it.

## Features

- **Deep comparison** of objects, arrays, and primitives.
- **Three array comparison strategies**: `byIndex` (default), `lcs` (minimal diff via Longest Common Subsequence), and `unordered` (multiset match).
- **Case-insensitive** key and/or value matching.
- **Numeric-string equality** — optionally treat `"1"` and `1` as equal.
- **Path tracking** with both segment-array and dot-notation forms.
- **Zero runtime dependencies** — pure standard library.
- **CLI** with table or JSON output, reading from inline strings or files.

## Installation

```bash
pip install compare-json-py
```

## Quick Start

### Library

```python
from compare_json import compareJSON, CompareOptions

base = {"name": "Alice", "age": 30}
contrast = {"name": "Bob", "age": "30", "email": "bob@test.com"}

diffs = compareJSON(base, contrast)
for d in diffs:
    print(d.path_string, d.path_belongs_to, d.diff_type.value)
# name   both     valueChanged
# age    both     typeChanged
# email  contrast added

# With options
options = CompareOptions(
    array_compare_method="lcs",  # or "byIndex", "unordered"
    key_case_insensitive=True,
    value_case_insensitive=True,
    numeric_string_equals_number=True,
)
diffs = compareJSON(base, contrast, options)
```

### CLI

```bash
# Compare JSON files
compare-json base.json contrast.json
```

```
┌──────────────┬──────────────┐
│ Key          │ Change Type  │
├──────────────┼──────────────┤
│ (Base) a     │ valueChanged │
│ (Base) b     │ deleted      │
│ (Contrast) c │ added        │
└──────────────┴──────────────┘
```

```bash
# Compare inline JSON strings
compare-json '{"a":1}' '{"a":2,"b":3}'

# Array strategies and case-insensitive matching
compare-json base.json contrast.json -a lcs -k -v

# Machine-readable JSON output
compare-json base.json contrast.json -j

# Write the report to a file
compare-json base.json contrast.json -o diff.txt
```

## Options

| Flag | Description |
|------|-------------|
| `-a, --array-compare-method` | Array comparison strategy: `byIndex` (default), `lcs`, `unordered` |
| `-k, --key-case-insensitive` | Compare object keys case-insensitively |
| `-v, --value-case-insensitive` | Compare string values case-insensitively |
| `--numeric-string-equals-number` | Treat numeric strings as equal to numbers |
| `-j, --json-export` | Output the differences as JSON |
| `-o, --output FILE` | Write output to a file instead of stdout |

## Differences from the TypeScript reference

This port intentionally uses native Python semantics instead of replicating JavaScript
quirks. See [COMPATIBILITY.md](./COMPATIBILITY.md) for the full policy. In short:

- Numeric strings are parsed with `float()` (no JS `Number()` quirks like `"" → 0` or hex;
  note Python accepts underscores, e.g. `"1_000"`).
- Object keys keep insertion order, but integer-like keys are not reordered to the front
  the way JS `Object.keys` does — difference entries may be ordered differently than the
  TS output; content is the same.
- Integers beyond 2^53 are compared exactly (Python ints are unbounded).
- Key existence checks look at own keys only (the TS reference's `in`-operator
  prototype-chain behavior is a bug and is not reproduced).
- `json.loads` accepts `NaN` / `Infinity` literals, which the TS CLI rejects as invalid
  JSON.

## Development

```bash
# install in editable mode with test dependencies
pip install -e . pytest

# run unit tests and CLI end-to-end tests
pytest
```

The repo layout:

```
compare_json/
├── compare.py   # core diff engine
├── types.py     # CompareOptions / JSONValueDifference / enums
├── utils.py     # type + path helpers
└── cli.py       # CLI entry point (console script: compare-json)
tests/
├── test_compare.py    # unit tests
└── test_cli_e2e.py    # CLI end-to-end tests
```

## Publishing to PyPI

```bash
# Install build tools
pip install build twine

# Build
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## License

MIT
