from typing import Any, List, Optional

from .types import CompareOptions, JSONValueDifference, JSONValueDiffType
from .utils import format_path, get_value_type


def compareJSON(
    base_json: Any,
    contrast_json: Any,
    options: Optional[CompareOptions] = None,
) -> List[JSONValueDifference]:
    if options is None:
        options = CompareOptions()
    return _compare_value(base_json, contrast_json, [], options)


def _compare_value(
    base: Any,
    contrast: Any,
    path_segments: List[str],
    options: CompareOptions,
) -> List[JSONValueDifference]:
    base_type = get_value_type(base)
    contrast_type = get_value_type(contrast)

    if base_type == "object" and contrast_type == "object":
        return _compare_object(base, contrast, path_segments, options)

    if base_type == "array" and contrast_type == "array":
        return _compare_array(base, contrast, path_segments, options)

    if base_type != contrast_type:
        if options.numeric_string_equals_number:
            if _is_numeric_string_match(base, contrast, base_type, contrast_type):
                return []
        return [
            JSONValueDifference(
                path_segments=list(path_segments),
                path_string=format_path(path_segments),
                path_belongs_to="both",
                diff_type=JSONValueDiffType.TYPE_CHANGED,
            )
        ]

    if base_type == "string" and options.value_case_insensitive:
        if base.lower() != contrast.lower():
            return [
                JSONValueDifference(
                    path_segments=list(path_segments),
                    path_string=format_path(path_segments),
                    path_belongs_to="both",
                    diff_type=JSONValueDiffType.VALUE_CHANGED,
                )
            ]
        return []

    if base != contrast:
        return [
            JSONValueDifference(
                path_segments=list(path_segments),
                path_string=format_path(path_segments),
                path_belongs_to="both",
                diff_type=JSONValueDiffType.VALUE_CHANGED,
            )
        ]

    return []


def _is_numeric_string_match(base: Any, contrast: Any, base_type: str, contrast_type: str) -> bool:
    if base_type == "string" and contrast_type == "number":
        try:
            return float(base) == contrast
        except (ValueError, TypeError):
            return False
    if base_type == "number" and contrast_type == "string":
        try:
            return base == float(contrast)
        except (ValueError, TypeError):
            return False
    return False


def _compare_object(
    base: dict,
    contrast: dict,
    path_segments: List[str],
    options: CompareOptions,
) -> List[JSONValueDifference]:
    diffs: List[JSONValueDifference] = []
    matched_contrast_keys: set = set()

    contrast_key_map = None
    if options.key_case_insensitive:
        contrast_key_map = _build_case_insensitive_map(contrast)

    for key in base:
        base_value = base[key]
        matched_key = None

        if options.key_case_insensitive:
            matched_key = _find_unmatched_key(contrast_key_map, key.lower(), matched_contrast_keys)
        else:
            if key in contrast:
                matched_key = key

        path = path_segments + [key]

        if matched_key is None:
            diffs.append(
                JSONValueDifference(
                    path_segments=path,
                    path_string=format_path(path),
                    path_belongs_to="base",
                    diff_type=JSONValueDiffType.DELETED,
                )
            )
        else:
            matched_contrast_keys.add(matched_key)
            diffs.extend(_compare_value(base_value, contrast[matched_key], path, options))

    for key in contrast:
        if key in matched_contrast_keys:
            continue
        has_match = False
        if options.key_case_insensitive:
            for bk in base:
                if bk.lower() == key.lower():
                    has_match = True
                    break
        else:
            has_match = key in base
        if not has_match:
            path = path_segments + [key]
            diffs.append(
                JSONValueDifference(
                    path_segments=path,
                    path_string=format_path(path),
                    path_belongs_to="contrast",
                    diff_type=JSONValueDiffType.ADDED,
                )
            )

    return diffs


def _build_case_insensitive_map(obj: dict) -> dict:
    m = {}
    for k in obj:
        lower = k.lower()
        if lower not in m:
            m[lower] = []
        m[lower].append(k)
    return m


def _find_unmatched_key(m: dict, lower_key: str, matched: set) -> Optional[str]:
    candidates = m.get(lower_key)
    if not candidates:
        return None
    for k in candidates:
        if k not in matched:
            return k
    return None


def _compare_array(
    base: list,
    contrast: list,
    path_segments: List[str],
    options: CompareOptions,
) -> List[JSONValueDifference]:
    method = options.array_compare_method
    if method == "lcs":
        return _compare_array_lcs(base, contrast, path_segments, options)
    elif method == "unordered":
        return _compare_array_unordered(base, contrast, path_segments, options)
    else:
        return _compare_array_by_index(base, contrast, path_segments, options)


def _compare_array_by_index(
    base: list,
    contrast: list,
    path_segments: List[str],
    options: CompareOptions,
) -> List[JSONValueDifference]:
    diffs: List[JSONValueDifference] = []
    min_len = min(len(base), len(contrast))

    for i in range(min_len):
        path = path_segments + [f"[{i}]"]
        diffs.extend(_compare_value(base[i], contrast[i], path, options))

    for i in range(min_len, len(base)):
        path = path_segments + [f"[{i}]"]
        diffs.append(
            JSONValueDifference(
                path_segments=path,
                path_string=format_path(path),
                path_belongs_to="base",
                diff_type=JSONValueDiffType.DELETED,
            )
        )

    for i in range(min_len, len(contrast)):
        path = path_segments + [f"[{i}]"]
        diffs.append(
            JSONValueDifference(
                path_segments=path,
                path_string=format_path(path),
                path_belongs_to="contrast",
                diff_type=JSONValueDiffType.ADDED,
            )
        )

    return diffs


def _deep_equal(a: Any, b: Any, options: CompareOptions) -> bool:
    return len(_compare_value(a, b, [], options)) == 0


def _compare_array_lcs(
    base: list,
    contrast: list,
    path_segments: List[str],
    options: CompareOptions,
) -> List[JSONValueDifference]:
    m, n = len(base), len(contrast)

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if _deep_equal(base[i - 1], contrast[j - 1], options):
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    matched_base: set = set()
    matched_contrast: set = set()
    i, j = m, n
    while i > 0 and j > 0:
        if _deep_equal(base[i - 1], contrast[j - 1], options):
            matched_base.add(i - 1)
            matched_contrast.add(j - 1)
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    diffs: List[JSONValueDifference] = []
    for i in range(m):
        if i not in matched_base:
            path = path_segments + [f"[{i}]"]
            diffs.append(
                JSONValueDifference(
                    path_segments=path,
                    path_string=format_path(path),
                    path_belongs_to="base",
                    diff_type=JSONValueDiffType.DELETED,
                )
            )

    for j in range(n):
        if j not in matched_contrast:
            path = path_segments + [f"[{j}]"]
            diffs.append(
                JSONValueDifference(
                    path_segments=path,
                    path_string=format_path(path),
                    path_belongs_to="contrast",
                    diff_type=JSONValueDiffType.ADDED,
                )
            )

    return diffs


def _compare_array_unordered(
    base: list,
    contrast: list,
    path_segments: List[str],
    options: CompareOptions,
) -> List[JSONValueDifference]:
    diffs: List[JSONValueDifference] = []
    matched_contrast: set = set()

    for i, base_item in enumerate(base):
        found = False
        for j, contrast_item in enumerate(contrast):
            if j in matched_contrast:
                continue
            if _deep_equal(base_item, contrast_item, options):
                matched_contrast.add(j)
                found = True
                break
        if not found:
            path = path_segments + [f"[{i}]"]
            diffs.append(
                JSONValueDifference(
                    path_segments=path,
                    path_string=format_path(path),
                    path_belongs_to="base",
                    diff_type=JSONValueDiffType.DELETED,
                )
            )

    for j in range(len(contrast)):
        if j not in matched_contrast:
            path = path_segments + [f"[{j}]"]
            diffs.append(
                JSONValueDifference(
                    path_segments=path,
                    path_string=format_path(path),
                    path_belongs_to="contrast",
                    diff_type=JSONValueDiffType.ADDED,
                )
            )

    return diffs
