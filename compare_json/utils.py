from typing import Any
import re

_INDEX_SEGMENT_RE = re.compile(r"^\[\d+\]$")


def get_value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "undefined"


def format_path(segments: list[str]) -> str:
    if not segments:
        return ""
    result = segments[0]
    for seg in segments[1:]:
        # Array-index segments like "[0]" are appended directly,
        # everything else is joined with a dot.
        if _INDEX_SEGMENT_RE.match(seg):
            result += seg
        else:
            result += "." + seg
    return result
