"""Tests for element commands."""

import os
import sys

import pytest
import responses

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import vidu_client as client
from commands.elements import preprocess, create, list_elements, search


@responses.activate
def test_preprocess_success():
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/vidu/v1/material/elements/pre-process",
        json={"id": "123", "recaption": {"description": "test"}},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        preprocess(
            name="test",
            elem_type="user",
            images=["ssupload:?id=111"],
        )
    assert exc.value.code == 0


@responses.activate
def test_create_success():
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/vidu/v1/material/elements",
        json={"id": "456", "version": "1"},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        create(
            elem_id="123",
            name="test",
            modality="image",
            elem_type="user",
            images=["ssupload:?id=111"],
            version="0",
            description="test description",
        )
    assert exc.value.code == 0


def test_preprocess_too_many_images():
    with pytest.raises(SystemExit) as exc:
        preprocess(
            name="test",
            elem_type="user",
            images=["a", "b", "c", "d"],
        )
    assert exc.value.code == 1


def test_preprocess_no_images():
    with pytest.raises(SystemExit) as exc:
        preprocess(
            name="test",
            elem_type="user",
            images=[],
        )
    assert exc.value.code == 1


@responses.activate
def test_search_success():
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/vidu/v1/material/share_elements/feed",
        json={"share_elements": [{"element": {"id": "789", "version": "1", "name": "tiger"}}], "next_page_token": ""},
        status=200,
    )

    with pytest.raises(SystemExit) as exc:
        search(keyword="tiger")
    assert exc.value.code == 0


def test_search_missing_keyword():
    with pytest.raises(SystemExit) as exc:
        search(keyword="")
    assert exc.value.code == 1
