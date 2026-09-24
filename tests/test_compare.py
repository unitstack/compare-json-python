import pytest
from compare_json import compareJSON, CompareOptions, JSONValueDifference, JSONValueDiffType


class TestPrimitiveValueComparison:
    def test_same_values(self):
        assert compareJSON("test", "test") == []
        assert compareJSON(123, 123) == []
        assert compareJSON(True, True) == []
        assert compareJSON(None, None) == []

    def test_value_changes(self):
        result = compareJSON("old", "new")
        assert len(result) == 1
        assert result[0].path_segments == []
        assert result[0].path_string == ""
        assert result[0].path_belongs_to == "both"
        assert result[0].diff_type == JSONValueDiffType.VALUE_CHANGED

    def test_type_changes(self):
        result = compareJSON("string", 123)
        assert len(result) == 1
        assert result[0].path_belongs_to == "both"
        assert result[0].diff_type == JSONValueDiffType.TYPE_CHANGED


class TestObjectComparison:
    def test_deleted_keys(self):
        result = compareJSON({"a": 1, "b": 2}, {"a": 1})
        assert len(result) == 1
        assert result[0].path_segments == ["b"]
        assert result[0].path_string == "b"
        assert result[0].path_belongs_to == "base"
        assert result[0].diff_type == JSONValueDiffType.DELETED

    def test_added_keys(self):
        result = compareJSON({"a": 1}, {"a": 1, "b": 2})
        assert len(result) == 1
        assert result[0].path_segments == ["b"]
        assert result[0].path_string == "b"
        assert result[0].path_belongs_to == "contrast"
        assert result[0].diff_type == JSONValueDiffType.ADDED

    def test_value_changes_in_nested_objects(self):
        result = compareJSON({"nested": {"value": "old"}}, {"nested": {"value": "new"}})
        assert len(result) == 1
        assert result[0].path_segments == ["nested", "value"]
        assert result[0].path_string == "nested.value"
        assert result[0].path_belongs_to == "both"
        assert result[0].diff_type == JSONValueDiffType.VALUE_CHANGED

    def test_multiple_differences(self):
        result = compareJSON({"a": 1, "b": "old", "c": True}, {"a": 1, "b": "new", "d": False})
        assert len(result) == 3
        assert result[0].path_string == "b"
        assert result[0].diff_type == JSONValueDiffType.VALUE_CHANGED
        assert result[1].path_string == "c"
        assert result[1].path_belongs_to == "base"
        assert result[1].diff_type == JSONValueDiffType.DELETED
        assert result[2].path_string == "d"
        assert result[2].path_belongs_to == "contrast"
        assert result[2].diff_type == JSONValueDiffType.ADDED


class TestArrayComparison:
    def test_deleted_elements(self):
        result = compareJSON([1, 2, 3], [1, 2])
        assert len(result) == 1
        assert result[0].path_segments == ["[2]"]
        assert result[0].path_string == "[2]"
        assert result[0].path_belongs_to == "base"
        assert result[0].diff_type == JSONValueDiffType.DELETED

    def test_added_elements(self):
        result = compareJSON([1, 2], [1, 2, 3])
        assert len(result) == 1
        assert result[0].path_segments == ["[2]"]
        assert result[0].path_string == "[2]"
        assert result[0].path_belongs_to == "contrast"
        assert result[0].diff_type == JSONValueDiffType.ADDED

    def test_value_changes_in_array_elements(self):
        result = compareJSON([1, "old", True], [1, "new", True])
        assert len(result) == 1
        assert result[0].path_segments == ["[1]"]
        assert result[0].path_string == "[1]"
        assert result[0].path_belongs_to == "both"
        assert result[0].diff_type == JSONValueDiffType.VALUE_CHANGED

    def test_nested_arrays(self):
        result = compareJSON([[1, 2], [3, 4]], [[1, 2], [3, "5"]])
        assert len(result) == 1
        assert result[0].path_segments == ["[1]", "[1]"]
        assert result[0].path_string == "[1][1]"
        assert result[0].path_belongs_to == "both"
        assert result[0].diff_type == JSONValueDiffType.TYPE_CHANGED


class TestLCSArrayComparison:
    def test_shifted_arrays(self):
        opts = CompareOptions(array_compare_method="lcs")
        result = compareJSON(["a", "b", "c"], ["b", "c", "d"], opts)
        assert len(result) == 2
        assert result[0].path_string == "[0]"
        assert result[0].path_belongs_to == "base"
        assert result[0].diff_type == JSONValueDiffType.DELETED
        assert result[1].path_string == "[2]"
        assert result[1].path_belongs_to == "contrast"
        assert result[1].diff_type == JSONValueDiffType.ADDED

    def test_identical_arrays(self):
        opts = CompareOptions(array_compare_method="lcs")
        result = compareJSON([1, 2, 3], [1, 2, 3], opts)
        assert result == []

    def test_empty_arrays(self):
        opts = CompareOptions(array_compare_method="lcs")
        assert compareJSON([], [], opts) == []

    def test_no_common_elements(self):
        opts = CompareOptions(array_compare_method="lcs")
        result = compareJSON([1, 2, 3], [4, 5, 6], opts)
        assert len(result) == 6

    def test_objects_in_arrays(self):
        opts = CompareOptions(array_compare_method="lcs")
        result = compareJSON(
            [{"id": 1}, {"id": 2}, {"id": 3}],
            [{"id": 2}, {"id": 3}, {"id": 4}],
            opts,
        )
        assert len(result) == 2
        assert result[0].path_string == "[0]"
        assert result[0].path_belongs_to == "base"
        assert result[1].path_string == "[2]"
        assert result[1].path_belongs_to == "contrast"

    def test_base_has_extra_middle_element(self):
        opts = CompareOptions(array_compare_method="lcs")
        result = compareJSON(["a", "x", "b"], ["a", "b"], opts)
        assert len(result) == 1
        assert result[0].path_string == "[1]"
        assert result[0].path_belongs_to == "base"
        assert result[0].diff_type == JSONValueDiffType.DELETED


class TestUnorderedArrayComparison:
    def test_reordered_arrays_equal(self):
        opts = CompareOptions(array_compare_method="unordered")
        result = compareJSON(["a", "b", "c"], ["c", "b", "a"], opts)
        assert result == []

    def test_added_and_deleted_ignoring_order(self):
        opts = CompareOptions(array_compare_method="unordered")
        result = compareJSON(["a", "b", "c"], ["a", "c", "d"], opts)
        assert len(result) == 2
        assert result[0].path_string == "[1]"
        assert result[0].path_belongs_to == "base"
        assert result[0].diff_type == JSONValueDiffType.DELETED
        assert result[1].path_string == "[2]"
        assert result[1].path_belongs_to == "contrast"
        assert result[1].diff_type == JSONValueDiffType.ADDED

    def test_duplicate_values(self):
        opts = CompareOptions(array_compare_method="unordered")
        result = compareJSON(["a", "a", "b"], ["a", "b", "b"], opts)
        assert len(result) == 2
        assert result[0].path_belongs_to == "base"
        assert result[1].path_belongs_to == "contrast"

    def test_objects_ignoring_order(self):
        opts = CompareOptions(array_compare_method="unordered")
        result = compareJSON(
            [{"id": 1}, {"id": 2}, {"id": 3}],
            [{"id": 3}, {"id": 1}, {"id": 2}],
            opts,
        )
        assert result == []


class TestValueCaseInsensitive:
    def test_different_case_strings_equal(self):
        opts = CompareOptions(value_case_insensitive=True)
        assert compareJSON("Hello", "hello", opts) == []

    def test_still_detect_different_values(self):
        opts = CompareOptions(value_case_insensitive=True)
        result = compareJSON("hello", "world", opts)
        assert len(result) == 1
        assert result[0].diff_type == JSONValueDiffType.VALUE_CHANGED

    def test_ignore_case_in_objects(self):
        opts = CompareOptions(value_case_insensitive=True)
        result = compareJSON({"name": "Alice"}, {"name": "alice"}, opts)
        assert result == []

    def test_ignore_case_in_arrays(self):
        opts = CompareOptions(value_case_insensitive=True)
        result = compareJSON(["Hello", "World"], ["hello", "world"], opts)
        assert result == []


class TestKeyCaseInsensitive:
    def test_match_keys_with_different_cases(self):
        opts = CompareOptions(key_case_insensitive=True)
        result = compareJSON({"Name": "Alice"}, {"name": "Alice"}, opts)
        assert result == []

    def test_match_nested_keys(self):
        opts = CompareOptions(key_case_insensitive=True)
        result = compareJSON(
            {"User": {"Name": "Alice"}},
            {"user": {"name": "Alice"}},
            opts,
        )
        assert result == []

    def test_detect_deleted_keys(self):
        opts = CompareOptions(key_case_insensitive=True)
        result = compareJSON({"a": 1, "B": 2}, {"A": 1}, opts)
        assert len(result) == 1
        assert result[0].path_string == "B"
        assert result[0].path_belongs_to == "base"
        assert result[0].diff_type == JSONValueDiffType.DELETED

    def test_detect_added_keys(self):
        opts = CompareOptions(key_case_insensitive=True)
        result = compareJSON({"a": 1}, {"A": 1, "b": 2}, opts)
        assert len(result) == 1
        assert result[0].path_string == "b"
        assert result[0].path_belongs_to == "contrast"
        assert result[0].diff_type == JSONValueDiffType.ADDED

    def test_multiple_keys_same_lowercase(self):
        opts = CompareOptions(key_case_insensitive=True)
        result = compareJSON({"name": "a", "Name": "b"}, {"NAME": "a", "name": "b"}, opts)
        assert result == []


class TestNumericStringEqualsNumber:
    def test_numeric_string_equals_number(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        assert compareJSON("123", 123, opts) == []

    def test_number_equals_numeric_string(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        assert compareJSON(456, "456", opts) == []

    def test_non_numeric_string_not_equal(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        result = compareJSON("abc", 123, opts)
        assert len(result) == 1
        assert result[0].diff_type == JSONValueDiffType.TYPE_CHANGED

    def test_floating_point(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        assert compareJSON("3.14", 3.14, opts) == []

    def test_negative_numbers(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        assert compareJSON("-42", -42, opts) == []

    def test_in_nested_objects(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        assert compareJSON({"count": "100"}, {"count": 100}, opts) == []

    def test_in_arrays(self):
        opts = CompareOptions(numeric_string_equals_number=True)
        assert compareJSON(["1", "2", "3"], [1, 2, 3], opts) == []

    def test_with_unordered_arrays(self):
        opts = CompareOptions(
            numeric_string_equals_number=True,
            array_compare_method="unordered",
        )
        assert compareJSON(["1", "2", "3"], [3, 2, 1], opts) == []

    def test_with_lcs_arrays(self):
        opts = CompareOptions(
            numeric_string_equals_number=True,
            array_compare_method="lcs",
        )
        result = compareJSON(["1", "2", "3"], [2, 3, 4], opts)
        assert len(result) == 2
        assert result[0].path_string == "[0]"
        assert result[0].path_belongs_to == "base"
        assert result[1].path_string == "[2]"
        assert result[1].path_belongs_to == "contrast"
