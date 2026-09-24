from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Literal, Optional


class JSONValueDiffType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    TYPE_CHANGED = "typeChanged"
    VALUE_CHANGED = "valueChanged"


@dataclass
class JSONValueDifference:
    path_segments: List[str]
    path_string: str
    path_belongs_to: Literal["base", "contrast", "both"]
    diff_type: JSONValueDiffType


@dataclass
class CompareOptions:
    array_compare_method: Literal["byIndex", "lcs", "unordered"] = "byIndex"
    key_case_insensitive: bool = False
    value_case_insensitive: bool = False
    numeric_string_equals_number: bool = False
