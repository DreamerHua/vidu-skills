"""Task commands: submit, get, sse."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import vidu_client as client
import validators


def _load_json_arg(arg: str) -> dict:
    """Load JSON from string or @file.json syntax."""
    if arg.startswith("@"):
        path = arg[1:]
        if not os.path.isfile(path):
            client.fail("client_error", f"JSON file not found: {path}")
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            client.fail("client_error", f"Invalid JSON in file {path}: {e}")
    else:
        try:
            return json.loads(arg)
        except json.JSONDecodeError as e:
            client.fail("client_error", f"Invalid JSON: {e}")


def submit(task_type: str, prompt: str, images: list, materials: list,
           duration: int, model_version: str, aspect_ratio: str = None,
           transition: str = None, resolution: str = None, sample_count: int = 1,
           codec: str = "h265", movement_amplitude: str = "auto",
           schedule_mode: str = "normal"):
    """Submit task with CLI parameters."""

    # Build prompts array
    prompts = [{"type": "text", "content": prompt}]

    # Add image prompts
    for img in images:
        prompts.append({"type": "image", "content": img})

    # Add material prompts
    for mat in materials:
        parts = mat.split(":")
        if len(parts) != 3:
            client.fail("client_error", f"Invalid material format '{mat}'. Expected 'name:id:version'")
        name, mat_id, mat_version = parts
        prompts.append({
            "type": "material",
            "name": name,
            "material": {"id": mat_id, "version": mat_version}
        })

    # Build body
    body = {
        "type": task_type,
        "input": {
            "prompts": prompts,
            "editor_mode": "normal",
            "enhance": True
        },
        "settings": {
            "duration": duration,
            "model_version": model_version,
            "sample_count": sample_count,
            "schedule_mode": schedule_mode,
            "codec": codec,
        }
    }

    # Add optional settings
    body["settings"]["resolution"] = resolution
    if aspect_ratio:
        body["settings"]["aspect_ratio"] = aspect_ratio
    if transition:
        body["settings"]["transition"] = transition
    if movement_amplitude != "auto":
        body["settings"]["movement_amplitude"] = movement_amplitude

    # Validate
    err = validators.validate_task_body(body)
    if err:
        client.fail("client_error", err)

    data = client.request_json("POST", f"{client.BASE_URL}/vidu/v1/tasks", json=body)
    task_id = str(data.get("id", ""))
    if not task_id:
        client.fail("parse_error", f"No task id in response: {data}")
    client.ok(task_id=task_id)


def get(task_id: str):
    data = client.request_json("GET", f"{client.BASE_URL}/vidu/v1/tasks/{task_id}")
    state = data.get("state", "")
    result = {"task_id": task_id, "state": state}

    if state == "success":
        creations = data.get("creations") or []
        result["media_urls"] = [c["nomark_uri"] for c in creations if c.get("nomark_uri")]
    elif state == "failed":
        result["err_code"] = data.get("err_code", "")
        result["err_msg"] = data.get("err_msg", "")

    client.ok(**result)


def sse(task_id: str):
    """Stream SSE events directly to stdout."""
    import requests as req

    url = f"{client.BASE_URL}/vidu/v1/tasks/state?id={task_id}"
    headers = client.get_headers({"Accept": "text/event-stream"})
    try:
        with req.get(url, headers=headers, stream=True, timeout=300) as resp:
            if resp.status_code >= 400:
                code, msg = client._parse_error_body(resp)
                client.fail("http_error", msg, http_status=resp.status_code, code=code or None)
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    print(line, flush=True)
    except req.exceptions.ConnectionError as e:
        client.fail("network_error", str(e))
    except req.exceptions.Timeout:
        client.fail("network_error", "timeout")
