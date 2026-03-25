"""Element commands: preprocess, create, list, search."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import vidu_client as client
import validators


def _load_json_arg(arg: str) -> dict:
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


def preprocess(name: str, elem_type: str, images: list):
    """Preprocess element with CLI parameters."""
    if not images or len(images) > 3:
        client.fail("client_error", "Must provide 1-3 images")

    components = []
    for i, img in enumerate(images):
        components.append({
            "content": img,
            "src_img": img,
            "content_type": "image",
            "type": "main" if i == 0 else "auxiliary"
        })

    body = {
        "components": components,
        "name": name,
        "type": elem_type
    }

    err = validators.validate_element_preprocess(body)
    if err:
        client.fail("client_error", err)
    data = client.request_json("POST", f"{client.BASE_URL}/vidu/v1/material/elements/pre-process", json=body)
    client.ok(**data)


def create(elem_id: str, name: str, modality: str, elem_type: str,
           images: list, version: str, description: str):
    """Create element with CLI parameters."""
    if not images or len(images) > 3:
        client.fail("client_error", "Must provide 1-3 images")

    components = []
    for i, img in enumerate(images):
        components.append({
            "content": img,
            "src_img": img,
            "content_type": "image",
            "type": "main" if i == 0 else "auxiliary"
        })

    body = {
        "id": elem_id,
        "name": name,
        "modality": modality,
        "type": elem_type,
        "components": components,
        "version": version,
        "recaption": {
            "description": description
        }
    }

    err = validators.validate_element_create(body)
    if err:
        client.fail("client_error", err)
    data = client.request_json("POST", f"{client.BASE_URL}/vidu/v1/material/elements", json=body)
    element_id = str(data.get("id", ""))
    version = str(data.get("version", ""))
    client.ok(id=element_id, version=version, raw=data)


def list_elements(keyword: str = None, page: int = 0, pagesz: int = 20):
    params = {"pager.page": page, "pager.pagesz": pagesz, "modalities": "image"}
    if keyword:
        params["keyword"] = keyword
    data = client.request_json("GET", f"{client.BASE_URL}/vidu/v1/material/elements/personal", params=params)
    elements = data.get("elements") or []
    items = [{"id": str(e.get("id", "")), "version": str(e.get("version", "")), "name": e.get("name", "")} for e in elements]
    client.ok(elements=items, next_page_token=data.get("next_page_token", ""))


def search(keyword: str, pagesz: int = 20, sort_by: str = "recommend", page_token: str = ""):
    if not keyword:
        client.fail("client_error", "--keyword is required for search")
    params = {
        "keyword": keyword,
        "pager.page_token": page_token,
        "pager.pagesz": pagesz,
        "modalities": "image",
        "sort_by": sort_by,
        "is_like": "false",
        "is_collect": "false",
    }
    data = client.request_json("GET", f"{client.BASE_URL}/vidu/v1/material/share_elements/feed", params=params)
    share_elements = data.get("share_elements") or []
    items = []
    for se in share_elements:
        el = se.get("element") or {}
        sh = se.get("share") or {}
        recaption = el.get("recaption") or {}
        items.append({
            "id": str(el.get("id", "")),
            "version": str(el.get("version", "")),
            "name": el.get("name", ""),
            "description": (recaption.get("description") or "")[:100],
            "category": sh.get("category_display") or [],
        })
    client.ok(elements=items, next_page_token=data.get("next_page_token", ""))
