"""Tests for task commands - focusing on state distinction and error handling."""

import json
import os
import sys

import pytest
import responses

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import vidu_client as client
from commands.tasks import submit, get


@responses.activate
def test_submit_success():
    """Successful submit returns task_id."""
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/vidu/v1/tasks",
        json={"id": "3202402178822691"},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        submit(
            task_type="text2video",
            prompt="test",
            images=[],
            materials=[],
            duration=5,
            model_version="3.2",
            aspect_ratio="16:9",
            transition="pro",
            resolution="1080p",
        )
    assert exc.value.code == 0


@responses.activate
def test_submit_422_invalid_param():
    """422 parameter error returns http_error with code."""
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/vidu/v1/tasks",
        json={"code": "invalid_param", "message": "duration out of range"},
        status=422,
    )

    with pytest.raises(SystemExit) as exc:
        submit(
            task_type="text2video",
            prompt="test",
            images=[],
            materials=[],
            duration=5,
            model_version="3.2",
        )
    assert exc.value.code == 1


@responses.activate
def test_get_success_state():
    """state=success returns media_urls."""
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/vidu/v1/tasks/123",
        json={"state": "success", "creations": [{"nomark_uri": "https://video.url"}]},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        get("123")
    assert exc.value.code == 0


@responses.activate
def test_get_failed_state():
    """state=failed returns ok=true with err_code/err_msg."""
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/vidu/v1/tasks/123",
        json={"state": "failed", "err_code": "quota_exceeded", "err_msg": "Quota exceeded"},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        get("123")
    assert exc.value.code == 0


@responses.activate
def test_get_processing_state():
    """state=processing returns ok=true without media_urls."""
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/vidu/v1/tasks/123",
        json={"state": "processing"},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        get("123")
    assert exc.value.code == 0


def test_submit_invalid_material_format():
    """Invalid material format returns client_error."""
    with pytest.raises(SystemExit) as exc:
        submit(
            task_type="character2video",
            prompt="test",
            images=[],
            materials=["bad_format"],
            duration=5,
            model_version="3.2",
        )
    assert exc.value.code == 1
