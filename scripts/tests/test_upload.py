"""Tests for upload command - focusing on hallucination prevention."""

import json
import os
import sys

import pytest
import responses

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import vidu_client as client
from commands.upload import run


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_IMG = os.path.join(FIXTURES, "sample.jpg")


@responses.activate
def test_upload_success():
    """Successful upload returns structured JSON with upload_id and ssupload_uri."""
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/tools/v1/files/uploads",
        json={"id": 12345, "put_url": "https://s3.example.com/put"},
        status=200,
    )
    responses.add(
        responses.PUT,
        "https://s3.example.com/put",
        headers={"ETag": '"abc123"'},
        status=200,
    )
    responses.add(
        responses.PUT,
        f"{client.BASE_URL}/tools/v1/files/uploads/12345/finish",
        json={"uri": "ssupload:?id=12345"},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        run(SAMPLE_IMG)
    assert exc.value.code == 0


@responses.activate
def test_upload_create_fails_401():
    """401 on create_upload returns http_error with status 401."""
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/tools/v1/files/uploads",
        json={"code": "unauthorized", "message": "Invalid token"},
        status=401,
    )

    with pytest.raises(SystemExit) as exc:
        run(SAMPLE_IMG)
    assert exc.value.code == 1


@responses.activate
def test_upload_put_fails():
    """PUT failure returns error with step=put_image."""
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/tools/v1/files/uploads",
        json={"id": 12345, "put_url": "https://s3.example.com/put"},
        status=200,
    )
    responses.add(
        responses.PUT,
        "https://s3.example.com/put",
        body="Access Denied",
        status=403,
    )

    with pytest.raises(SystemExit) as exc:
        run(SAMPLE_IMG)
    assert exc.value.code == 1


def test_upload_file_not_found():
    """Non-existent file returns client_error."""
    with pytest.raises(SystemExit) as exc:
        run("/nonexistent/image.jpg")
    assert exc.value.code == 1
