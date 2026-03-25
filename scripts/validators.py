"""Parameter validation for Vidu API."""

import json
import sys


# Valid task types
VALID_TASK_TYPES = {"text2image", "text2video", "img2video", "headtailimg2video", "reference2image", "character2video"}

# Model versions
VALID_MODEL_VERSIONS = {"3.0", "3.1", "3.2", "3.2_fast_m", "3.2_pro_m"}

# Resolutions by task type
RESOLUTION_SUPPORT = {
    "text2image": {"1080p", "2k", "4k"},
    "reference2image": {"1080p", "2k", "4k"},
    "text2video": {"1080p"},
    "img2video": {"1080p"},
    "headtailimg2video": {"1080p"},
    "character2video": {"1080p"},
}

# Aspect ratios
VALID_ASPECT_RATIOS = {"16:9", "9:16", "1:1"}

# Durations by model and type
DURATION_RANGES = {
    "text2video": {"3.0": (5, 5), "3.1": (2, 8), "3.2": (1, 16)},
    "img2video": {"3.0": (5, 5), "3.1": (2, 8), "3.2": (1, 16)},
    "headtailimg2video": {"3.0": (5, 5), "3.1": (2, 8), "3.2": (1, 16)},
    "character2video": {"3.0": (5, 5), "3.1": (2, 8), "3.1_pro": (-1, 8), "3.2": (1, 16)},
    "reference2image": {"3.1": (0, 0), "3.2_fast_m": (0, 0), "3.2_pro_m": (0, 0)},
    "text2image": {"3.1": (0, 0), "3.2_fast_m": (0, 0), "3.2_pro_m": (0, 0)},
}

# Model support by task type
MODEL_SUPPORT = {
    "text2image": {"3.1", "3.2_fast_m", "3.2_pro_m"},
    "text2video": {"3.0", "3.1", "3.2"},
    "img2video": {"3.0", "3.1", "3.2"},
    "headtailimg2video": {"3.0", "3.1", "3.2"},
    "reference2image": {"3.1", "3.2_fast_m", "3.2_pro_m"},
    "character2video": {"3.0", "3.1", "3.1_pro", "3.2"},
}


def validate_task_body(body: dict) -> str:
    """Validate task submission body. Return error message or empty string."""
    task_type = body.get("type", "")
    if not task_type:
        return "Missing required field: type"
    if task_type not in VALID_TASK_TYPES:
        return f"Invalid type '{task_type}'. Valid: {', '.join(sorted(VALID_TASK_TYPES))}"

    # Check input
    input_obj = body.get("input", {})
    if not isinstance(input_obj, dict):
        return "input must be an object"
    prompts = input_obj.get("prompts", [])
    if not prompts:
        return "input.prompts is required and must not be empty"
    if not isinstance(prompts, list):
        return "input.prompts must be an array"

    # Check settings
    settings = body.get("settings", {})
    if not isinstance(settings, dict):
        return "settings must be an object"

    model_version = settings.get("model_version", "2.0")
    if model_version not in VALID_MODEL_VERSIONS:
        return f"Invalid model_version '{model_version}'. Valid: {', '.join(sorted(VALID_MODEL_VERSIONS))}"

    # Check model supports this task type
    if model_version not in MODEL_SUPPORT.get(task_type, set()):
        return f"model_version {model_version} does not support {task_type}"

    # Check duration
    if task_type in DURATION_RANGES:
        duration = settings.get("duration", 0)
        min_d, max_d = DURATION_RANGES[task_type].get(model_version, (0, 0))
        if min_d > 0 and (duration < min_d or duration > max_d):
            return f"duration {duration} out of range [{min_d}, {max_d}] for {task_type} with {model_version}"

    # Check resolution (required)
    if "resolution" not in settings:
        return f"resolution is required for {task_type}"
    res = settings["resolution"]
    valid_res = RESOLUTION_SUPPORT.get(task_type, {"1080p"})
    if res not in valid_res:
        return f"Invalid resolution '{res}' for {task_type}. Valid: {', '.join(sorted(valid_res))}"

    # Check aspect_ratio (not for img2video, headtailimg2video, text2image)
    if task_type not in ("img2video", "headtailimg2video", "text2image") and "aspect_ratio" in settings:
        ar = settings["aspect_ratio"]
        if ar not in VALID_ASPECT_RATIOS:
            return f"Invalid aspect_ratio '{ar}'. Valid: {', '.join(VALID_ASPECT_RATIOS)}"

    # Check transition (only text2video and img2video/headtailimg2video support it)
    if "transition" in settings:
        if task_type in ("reference2image", "character2video", "text2image"):
            return f"{task_type} should not include transition"
        if task_type == "text2video" and model_version != "3.2":
            return f"text2video with {model_version} should not include transition (only 3.2 supports pro/speed)"
        if task_type == "img2video":
            transition = settings["transition"]
            valid_trans = {"creative", "stable"} if model_version == "3.0" else {"pro", "speed"}
            if transition not in valid_trans:
                return f"Invalid transition '{transition}' for img2video {model_version}. Valid: {', '.join(sorted(valid_trans))}"
        if task_type == "headtailimg2video":
            transition = settings["transition"]
            valid_trans = {"creative", "stable"} if model_version == "3.0" else {"pro", "speed"}
            if transition not in valid_trans:
                return f"Invalid transition '{transition}' for headtailimg2video {model_version}. Valid: {', '.join(sorted(valid_trans))}"

    # Check enhance
    if "enhance" not in input_obj:
        return "input.enhance is required (true or false)"

    return ""


def validate_element_preprocess(body: dict) -> str:
    """Validate element preprocess body."""
    if not isinstance(body, dict):
        return "body must be an object"
    if "components" not in body:
        return "Missing required field: components"
    if "name" not in body:
        return "Missing required field: name"
    if "type" not in body:
        return "Missing required field: type"

    components = body["components"]
    if not isinstance(components, list) or not components:
        return "components must be a non-empty array"
    if len(components) > 3:
        return "components must have at most 3 items"

    main_count = sum(1 for c in components if c.get("type") == "main")
    if main_count != 1:
        return "components must have exactly one item with type='main'"

    return ""


def validate_element_create(body: dict) -> str:
    """Validate element create body."""
    if not isinstance(body, dict):
        return "body must be an object"
    if "id" not in body:
        return "Missing required field: id (from preprocess response)"
    if "name" not in body:
        return "Missing required field: name"
    if "modality" not in body:
        return "Missing required field: modality"

    return ""


def validate_image_file(path: str) -> str:
    """Validate image file exists and is readable."""
    import os
    if not os.path.isfile(path):
        return f"Image file not found: {path}"
    if not os.access(path, os.R_OK):
        return f"Image file not readable: {path}"
    return ""


def compress_image_if_needed(path: str, max_size_mb: int = 10) -> str:
    """Compress image if larger than max_size_mb. Returns path to (possibly compressed) image."""
    import os
    from PIL import Image

    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb <= max_size_mb:
        return path

    # Compress
    try:
        img = Image.open(path)
        if img.mode == "RGBA":
            img = img.convert("RGB")

        # Save with progressive quality reduction until under limit
        quality = 95
        while quality >= 10:
            compressed_path = path.replace(".", "_compressed.")
            img.save(compressed_path, "JPEG", quality=quality, optimize=True)
            if os.path.getsize(compressed_path) / (1024 * 1024) <= max_size_mb:
                return compressed_path
            quality -= 5

        # If still too large, resize
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        compressed_path = path.replace(".", "_compressed.")
        img.save(compressed_path, "JPEG", quality=85, optimize=True)
        return compressed_path
    except Exception as e:
        raise ValueError(f"Failed to compress image: {e}")
