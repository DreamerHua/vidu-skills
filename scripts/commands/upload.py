"""Image upload command: Create upload → PUT bytes → Finish upload."""

import mimetypes
import os
import sys

# Allow running from scripts/ directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import vidu_client as client
import validators


def run(image_path: str):
    # Validate file
    err = validators.validate_image_file(image_path)
    if err:
        client.fail("client_error", err)

    # Compress if needed
    try:
        image_path = validators.compress_image_if_needed(image_path, max_size_mb=10)
    except ValueError as e:
        client.fail("client_error", str(e))

    # Read image and get dimensions
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception as e:
        client.fail("client_error", f"Cannot read image: {e}")

    # Detect content type
    mime, _ = mimetypes.guess_type(image_path)
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Step 1: Create upload
    body = {
        "metadata": {
            "image-width": str(width),
            "image-height": str(height),
        },
        "scene": "vidu",
    }
    data = client.request_json(
        "POST",
        f"{client.BASE_URL}/tools/v1/files/uploads",
        step="create_upload",
        json=body,
    )
    upload_id = data.get("id")
    put_url = data.get("put_url")
    if not upload_id or not put_url:
        client.fail("parse_error", f"Unexpected create_upload response: {data}", step="create_upload")

    # Step 2: PUT image bytes
    put_headers = {
        "Content-Type": mime,
        "x-amz-meta-image-width": str(width),
        "x-amz-meta-image-height": str(height),
    }
    put_resp = client.put_raw(put_url, image_bytes, put_headers, step="put_image")
    etag = put_resp.headers.get("ETag", "")

    # Step 3: Finish upload
    client.request_json(
        "PUT",
        f"{client.BASE_URL}/tools/v1/files/uploads/{upload_id}/finish",
        step="finish_upload",
        json={"etag": etag, "id": str(upload_id)},
    )

    client.ok(upload_id=str(upload_id), ssupload_uri=f"ssupload:?id={upload_id}")
