"""Comprehensive parameter combination tests against real Vidu API.

Usage:
    VIDU_TOKEN=xxx python3 -m pytest tests/test_param_combinations.py -v -s

Tests various valid and invalid parameter combinations.
Skipped if VIDU_TOKEN not set.
"""

import json
import os
import subprocess
import sys

import pytest

VIDU_CLI = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vidu-cli")
TOKEN = os.environ.get("VIDU_TOKEN", "")

pytestmark = pytest.mark.skipif(not TOKEN, reason="VIDU_TOKEN not set")


def run_cli(*args) -> dict:
    """Run vidu-cli and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, VIDU_CLI, *args],
        capture_output=True,
        text=True,
        env={**os.environ, "VIDU_TOKEN": TOKEN},
    )
    try:
        return {"exit_code": result.returncode, "data": json.loads(result.stdout)}
    except json.JSONDecodeError:
        return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


class TestValidTaskCombinations:
    """Test valid parameter combinations."""

    @pytest.mark.parametrize("task_type,model,duration", [
        ("text2video", "3.2", 5),
        ("text2video", "3.1", 8),
    ])
    def test_valid_task_types(self, task_type, model, duration):
        r = run_cli(
            "task", "submit",
            "--type", task_type,
            "--prompt", "test",
            "--duration", str(duration),
            "--model-version", model,
            "--aspect-ratio", "16:9",
            "--transition", "pro",
            "--resolution", "1080p",
        )
        assert r["exit_code"] == 0, f"Failed for {task_type}/{model}/{duration}: {r}"
        assert r["data"]["ok"] is True


class TestInvalidTaskCombinations:
    """Test invalid parameter combinations — should fail with client_error."""

    @pytest.mark.parametrize("task_type,model,duration", [
        ("text2video", "2.0", 10),   # invalid model version
        ("text2video", "3.2", 20),   # duration too long
        ("text2video", "3.2", 0),    # duration too short
    ])
    def test_invalid_combinations(self, task_type, model, duration):
        r = run_cli(
            "task", "submit",
            "--type", task_type,
            "--prompt", "test",
            "--duration", str(duration),
            "--model-version", model,
            "--aspect-ratio", "16:9",
            "--resolution", "1080p",
        )
        assert r["exit_code"] == 1, f"Should have failed for {task_type}/{model}/{duration}"
        assert r["data"]["ok"] is False
        assert r["data"]["error"]["type"] == "client_error"


class TestResolutionAspectRatio:
    """Test resolution and aspect ratio combinations."""

    @pytest.mark.parametrize("resolution,aspect_ratio", [
        ("1080p", "16:9"),
        ("1080p", "9:16"),
        ("1080p", "1:1"),
    ])
    def test_valid_resolution_aspect(self, resolution, aspect_ratio):
        r = run_cli(
            "task", "submit",
            "--type", "text2video",
            "--prompt", "test",
            "--duration", "5",
            "--model-version", "3.2",
            "--aspect-ratio", aspect_ratio,
            "--transition", "pro",
            "--resolution", resolution,
        )
        assert r["exit_code"] == 0, f"Failed for {resolution}/{aspect_ratio}: {r}"
