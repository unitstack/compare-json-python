import json
import os
import subprocess
import sys
import tempfile

import pytest


CLI_CMD = [sys.executable, "-m", "compare_json.cli"]


def run_cli(*args):
    result = subprocess.run(
        CLI_CMD + list(args),
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    return result


class TestCLIE2E:
    def test_show_help_when_no_arguments(self):
        result = run_cli()
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "compare-json" in result.stdout.lower()

    def test_show_version(self):
        result = run_cli("--version")
        assert result.returncode == 0
        assert "0.1.0" in result.stdout.strip()

    def test_error_on_invalid_json(self):
        result = run_cli("{invalid}", '{"a":1}')
        assert result.returncode != 0

    def test_compare_json_strings(self):
        result = run_cli('{"a":1}', '{"a":2}')
        assert result.returncode == 0
        assert "valueChanged" in result.stdout
        assert "(Base) a" in result.stdout

    def test_compare_json_files(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
            json.dump({"a": 1, "b": 2}, f1)
            f1_path = f1.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
            json.dump({"a": 2, "c": 3}, f2)
            f2_path = f2.name
        try:
            result = run_cli(f1_path, f2_path)
            assert result.returncode == 0
            assert "valueChanged" in result.stdout
            assert "deleted" in result.stdout
            assert "added" in result.stdout
        finally:
            os.unlink(f1_path)
            os.unlink(f2_path)

    def test_json_export(self):
        result = run_cli("--json-export", '{"a":1}', '{"a":2}')
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert len(parsed) == 1
        assert parsed[0]["diffType"] == "valueChanged"
        assert parsed[0]["pathBelongsTo"] == "both"
        assert parsed[0]["pathString"] == "a"

    def test_output_to_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name
        try:
            result = run_cli("-o", output_path, '{"a":1}', '{"a":2}')
            assert result.returncode == 0
            assert "Output written to" in result.stdout
            with open(output_path) as f:
                content = f.read()
            assert "valueChanged" in content
        finally:
            os.unlink(output_path)

    def test_array_compare_method_unordered(self):
        result = run_cli("-a", "unordered", "[1,2,3]", "[3,2,1]")
        assert result.returncode == 0
        assert "No differences found" in result.stdout

    def test_key_case_insensitive(self):
        result = run_cli("-k", '{"Name":"Alice"}', '{"name":"Alice"}')
        assert result.returncode == 0
        assert "No differences found" in result.stdout

    def test_value_case_insensitive(self):
        result = run_cli("-v", '{"status":"OK"}', '{"status":"ok"}')
        assert result.returncode == 0
        assert "No differences found" in result.stdout

    def test_numeric_string_equals_number(self):
        result = run_cli("--numeric-string-equals-number", '{"count":1}', '{"count":"1"}')
        assert result.returncode == 0
        assert "No differences found" in result.stdout

    def test_root_level_difference(self):
        result = run_cli("1", '"hello"')
        assert result.returncode == 0
        assert "(Root)" in result.stdout
        assert "typeChanged" in result.stdout

    def test_no_differences(self):
        result = run_cli('{"a":1}', '{"a":1}')
        assert result.returncode == 0
        assert "No differences found" in result.stdout

    def test_json_export_with_output_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name
        try:
            result = run_cli("-j", "-o", output_path, '{"a":1,"b":2}', '{"a":2,"c":3}')
            assert result.returncode == 0
            with open(output_path) as f:
                parsed = json.load(f)
            assert len(parsed) == 3
            assert parsed[0]["diffType"] == "valueChanged"
            assert parsed[1]["diffType"] == "deleted"
            assert parsed[1]["pathBelongsTo"] == "base"
            assert parsed[2]["diffType"] == "added"
            assert parsed[2]["pathBelongsTo"] == "contrast"
        finally:
            os.unlink(output_path)
