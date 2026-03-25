"""Vidu API HTTP client with unified headers, retry logic, and error normalization."""

import json
import os
import sys
import time

import requests


BASE_URL = os.environ.get("VIDU_BASE_URL", "https://service.vidu.cn")
TOKEN = os.environ.get("VIDU_TOKEN", "")

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


def fail(error_type: str, message: str, http_status: int = None, code: str = None, step: str = None):
    """Print structured error JSON and exit with code 1."""
    err = {"type": error_type, "message": message}
    if http_status is not None:
        err["http_status"] = http_status
    if code is not None:
        err["code"] = code
    if step is not None:
        err["step"] = step
    print(json.dumps({"ok": False, "error": err}))
    sys.exit(1)


def ok(**kwargs):
    """Print structured success JSON and exit with code 0."""
    print(json.dumps({"ok": True, **kwargs}))
    sys.exit(0)


def get_headers(extra: dict = None) -> dict:
    if not TOKEN:
        fail("client_error", "VIDU_TOKEN not set")
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": f"viduclawbot/1.0 (+{BASE_URL})",
    }
    if extra:
        headers.update(extra)
    return headers


def _parse_error_body(resp: requests.Response) -> tuple[str, str]:
    """Extract (code, message) from error response body."""
    try:
        body = resp.json()
        code = body.get("code") or body.get("err_code") or ""
        msg = body.get("message") or body.get("msg") or body.get("err_msg") or resp.text
        return str(code), str(msg)
    except Exception:
        return "", resp.text[:200]


def request(method: str, url: str, step: str = None, retries: bool = True, **kwargs) -> requests.Response:
    """Make an HTTP request with retry on 5xx. Returns response on success, calls fail() on error."""
    attempts = MAX_RETRIES if retries else 1
    last_exc = None

    for i in range(attempts):
        try:
            resp = requests.request(method, url, headers=get_headers(), timeout=30, **kwargs)
        except requests.exceptions.Timeout:
            last_exc = "timeout"
            if i < attempts - 1:
                time.sleep(RETRY_DELAYS[i])
            continue
        except requests.exceptions.ConnectionError as e:
            last_exc = str(e)
            if i < attempts - 1:
                time.sleep(RETRY_DELAYS[i])
            continue

        if resp.status_code >= 500 and i < attempts - 1:
            time.sleep(RETRY_DELAYS[i])
            continue

        if resp.status_code >= 400:
            code, msg = _parse_error_body(resp)
            fail("http_error", msg, http_status=resp.status_code, code=code or None, step=step)

        return resp

    if last_exc:
        fail("network_error", str(last_exc), step=step)

    # All retries exhausted on 5xx
    code, msg = _parse_error_body(resp)
    fail("http_error", msg, http_status=resp.status_code, code=code or None, step=step)


def request_json(method: str, url: str, step: str = None, **kwargs) -> dict:
    """Make request and parse JSON response."""
    resp = request(method, url, step=step, **kwargs)
    try:
        return resp.json()
    except Exception:
        fail("parse_error", f"Response is not valid JSON: {resp.text[:200]}", step=step)


def put_raw(url: str, data: bytes, headers: dict, step: str = None) -> requests.Response:
    """PUT raw bytes (for image upload). No auth headers — uses provided headers directly."""
    attempts = MAX_RETRIES
    last_exc = None

    for i in range(attempts):
        try:
            resp = requests.put(url, data=data, headers=headers, timeout=60)
        except requests.exceptions.Timeout:
            last_exc = "timeout"
            if i < attempts - 1:
                time.sleep(RETRY_DELAYS[i])
            continue
        except requests.exceptions.ConnectionError as e:
            last_exc = str(e)
            if i < attempts - 1:
                time.sleep(RETRY_DELAYS[i])
            continue

        if resp.status_code >= 500 and i < attempts - 1:
            time.sleep(RETRY_DELAYS[i])
            continue

        if resp.status_code >= 400:
            fail("http_error", f"PUT failed: {resp.text[:200]}", http_status=resp.status_code, step=step)

        return resp

    fail("network_error", str(last_exc), step=step)
