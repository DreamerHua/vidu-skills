"""Integration tests — run against real Vidu API.

Usage:
    VIDU_TOKEN=xxx python3 -m pytest tests/test_integration.py -v

These tests consume real API quota. Only run manually.
Skipped automatically if VIDU_TOKEN is not set.
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


class TestTaskFlow:
    """Test real task submit → get flow."""

    def test_submit_text2video(self):
        r = run_cli(
            "task", "submit",
            "--type", "text2video",
            "--prompt", "A cat walks in the snow",
            "--duration", "5",
            "--model-version", "3.2",
            "--aspect-ratio", "16:9",
            "--transition", "pro",
            "--resolution", "1080p",
        )
        assert r["exit_code"] == 0
        assert r["data"]["ok"] is True
        assert "task_id" in r["data"]
        # Save for next test
        TestTaskFlow.task_id = r["data"]["task_id"]

    def test_get_task(self):
        task_id = getattr(TestTaskFlow, "task_id", None)
        if not task_id:
            pytest.skip("No task_id from submit")
        r = run_cli("task", "get", task_id)
        assert r["exit_code"] == 0
        assert r["data"]["ok"] is True
        assert r["data"]["state"] in ("created", "queueing", "preparation", "scheduling", "processing", "success", "failed")


class TestErrorHandling:
    """Verify structured errors on bad input."""

    def test_submit_invalid_model_version(self):
        r = run_cli(
            "task", "submit",
            "--type", "text2video",
            "--prompt", "test",
            "--duration", "5",
            "--model-version", "9.9",
        )
        assert r["exit_code"] == 1
        assert r["data"]["ok"] is False
        assert r["data"]["error"]["type"] in ("client_error", "http_error")

    def test_get_nonexistent_task(self):
        r = run_cli("task", "get", "0000000000000000")
        assert r["exit_code"] == 1 or r["data"].get("state") == "failed"

    def test_upload_nonexistent_file(self):
        r = run_cli("upload", "/nonexistent/image.jpg")
        assert r["exit_code"] == 1
        assert r["data"]["ok"] is False
        assert r["data"]["error"]["type"] == "client_error"


class TestElements:
    """Test element search against real API."""

    def test_search_community(self):
        r = run_cli("element", "search", "--keyword", "cat", "--pagesz", "5")
        assert r["exit_code"] == 0
        assert r["data"]["ok"] is True
        assert "elements" in r["data"]
