"""Test 2K/4K support for text2image and reference2image."""

import json
import os
import subprocess
import sys

VIDU_CLI = os.path.join(os.path.dirname(__file__), "vidu-cli")
TOKEN = os.environ.get("VIDU_TOKEN", "")


def run_cli(*args) -> dict:
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


def test_text2image_resolution(resolution):
    """Test text2image with given resolution."""
    body = json.dumps({
        "type": "text2image",
        "input": {
            "prompts": [{"type": "text", "content": "a cat"}],
            "editor_mode": "normal",
            "enhance": True,
        },
        "settings": {
            "duration": 0,
            "resolution": resolution,
            "aspect_ratio": "16:9",
            "model_version": "2.0",
            "sample_count": 1,
            "use_trial": True,
        },
    })
    r = run_cli("task", "submit", body)
    return r


if __name__ == "__main__":
    if not TOKEN:
        print("VIDU_TOKEN not set")
        sys.exit(1)

    print("Testing text2image resolutions:")
    for res in ["1080p", "2K", "4K"]:
        r = test_text2image_resolution(res)
        if "data" not in r:
            print(f"  {res}: ✗ {r.get('stderr', 'unknown error')}")
        else:
            status = "✓" if r["exit_code"] == 0 else "✗"
            msg = r["data"].get("task_id") if r["exit_code"] == 0 else r["data"].get("error", {}).get("message", "unknown error")
            print(f"  {res}: {status} {msg}")
