import argparse
import json
import os
import sys
from typing import List

from .compare import compareJSON
from .types import CompareOptions, JSONValueDifference


def _parse_json_input(value: str, label: str) -> any:
    if os.path.isfile(value):
        with open(value, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                print(
                    f"Error: Failed to parse {label} file content from {value}, unable to parse as JSON. Error: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(
            f"Error: Failed to parse {label} input: if you passed a file path, the file was not found; if you passed a JSON string, it failed to parse. Error: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def _format_table(diffs: List[JSONValueDifference]) -> str:
    if not diffs:
        return "No differences found"

    rows = []
    for d in diffs:
        if not d.path_segments:
            key_str = "(Root)"
        else:
            prefix = "(Contrast)" if d.path_belongs_to == "contrast" else "(Base)"
            key_str = f"{prefix} {d.path_string}"
        rows.append((key_str, d.diff_type.value))

    key_width = max(len(r[0]) for r in rows)
    type_width = max(len(r[1]) for r in rows)
    key_width = max(key_width, len("Key"))
    type_width = max(type_width, len("Change Type"))

    top = f"\u250c{'─' * (key_width + 2)}\u252c{'─' * (type_width + 2)}\u2510"
    header = f"\u2502 {'Key'.ljust(key_width)} \u2502 {'Change Type'.ljust(type_width)} \u2502"
    sep = f"\u251c{'─' * (key_width + 2)}\u253c{'─' * (type_width + 2)}\u2524"
    bottom = f"\u2514{'─' * (key_width + 2)}\u2534{'─' * (type_width + 2)}\u2518"

    lines = [top, header, sep]
    for key, change in rows:
        lines.append(f"\u2502 {key.ljust(key_width)} \u2502 {change.ljust(type_width)} \u2502")
    lines.append(bottom)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog="compare-json",
        description="Compare two JSON files or strings",
    )
    parser.add_argument("base", nargs="?", help="Base JSON string or file path")
    parser.add_argument("contrast", nargs="?", help="Contrast JSON string or file path")
    parser.add_argument(
        "-a",
        "--array-compare-method",
        choices=["byIndex", "lcs", "unordered"],
        default="byIndex",
        help="Array comparison strategy (default: byIndex)",
    )
    parser.add_argument(
        "-k",
        "--key-case-insensitive",
        action="store_true",
        help="Compare object keys case-insensitively",
    )
    parser.add_argument(
        "-v",
        "--value-case-insensitive",
        action="store_true",
        help="Compare string values case-insensitively",
    )
    parser.add_argument(
        "--numeric-string-equals-number",
        action="store_true",
        help="Treat numeric strings as equal to numbers",
    )
    parser.add_argument(
        "-j",
        "--json-export",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write output to file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="0.1.0",
    )

    args = parser.parse_args()

    if args.base is None or args.contrast is None:
        parser.print_help()
        return

    base_json = _parse_json_input(args.base, "base")
    contrast_json = _parse_json_input(args.contrast, "contrast")

    options = CompareOptions(
        array_compare_method=args.array_compare_method,
        key_case_insensitive=args.key_case_insensitive,
        value_case_insensitive=args.value_case_insensitive,
        numeric_string_equals_number=args.numeric_string_equals_number,
    )

    diffs = compareJSON(base_json, contrast_json, options)

    if args.json_export:
        output = json.dumps(
            [
                {
                    "pathSegments": d.path_segments,
                    "pathString": d.path_string,
                    "pathBelongsTo": d.path_belongs_to,
                    "diffType": d.diff_type.value,
                }
                for d in diffs
            ],
            indent=2,
        )
    else:
        output = _format_table(diffs)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
