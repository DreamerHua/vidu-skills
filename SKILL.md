---
name: vidu-skills
description: Generate video and images by calling the official Vidu API via vidu CLI. Use when the user wants text-to-image (文生图), text-to-video (文生视频), image-to-video (图生视频), head-tail-image-to-video (首尾帧生视频), reference-to-image (参考生图), reference-to-video (参考生视频), Create References (创建参考资料), or to submit or check Vidu tasks. Requires VIDU_TOKEN and optional VIDU_BASE_URL.
compatibility: Requires Python 3 and vidu CLI (scripts/vidu-cli). Set VIDU_TOKEN in the environment; VIDU_BASE_URL optional (default https://service.vidu.cn).
version: 1.2.0
url: https://www.vidu.cn/
secrets:
  - VIDU_TOKEN
dependencies:
  - python3
---

# Vidu Video and Image Generation Skill (Vidu 音视频/图像生成技能)

Generate AI videos and images with Vidu (生数) via `vidu-cli` — text-to-image, text-to-video, image-to-video, start-end frame, reference-based generation, and material elements, up to 1080p/2K/4K.

## Execution model: use vidu CLI

**All execution is done via the `vidu-cli` CLI tool** (located at `scripts/vidu-cli`). All parameters are passed as CLI arguments (not JSON).

**Environment variables:**
- `VIDU_TOKEN` (required) — Your Vidu API token
- `VIDU_BASE_URL` (optional) — Default `https://service.vidu.cn` (mainland China); use `https://service.vidu.com` for overseas

**Output format:**
- All commands output single-line JSON to stdout
- Success: `{"ok": true, ...}` with exit code 0
- Failure: `{"ok": false, "error": {"type": "...", "http_status": ..., "code": "...", "message": "..."}}`  with exit code 1
- **CRITICAL: Never guess the cause of an error. Read the `error` object and report it exactly.**

**Error types:**
- `http_error` — API returned 4xx/5xx (includes `http_status`, `code`, `message`)
- `network_error` — Connection failed or timeout
- `parse_error` — Response is not valid JSON
- `client_error` — Local parameter error (file not found, missing VIDU_TOKEN)

**Main commands:**

| Command | Purpose |
|---------|---------|
| `vidu-cli upload <image_path>` | Upload image → returns `upload_id` and `ssupload_uri` |
| `vidu-cli task submit --type ... --prompt ... [options]` | Submit task → returns `task_id` |
| `vidu-cli task get <task_id>` | Query task → returns `state`, `media_urls` (if success) |
| `vidu-cli task sse <task_id>` | Stream SSE state events |
| `vidu-cli element preprocess --name ... --image ...` | Pre-process material element |
| `vidu-cli element create --id ... --name ... --image ... --description ...` | Create material element |
| `vidu-cli element list [--keyword kw]` | List personal elements |
| `vidu-cli element search --keyword kw` | Search community elements |

---

## Key Capabilities

- **text-to-image (文生图)** — Generate images from text prompts
- **text-to-video (文生视频)** — Generate videos from text prompts
- **image-to-video (图生视频)** — Generate videos from image + text
- **head-tail-image-to-video (首尾帧生视频)** — Generate videos with start/end frame control
- **reference-to-image (参考生图)** — Generate images using reference materials
- **reference-to-video (参考生视频)** — Generate videos using reference materials
- **Create References (创建主体)** — Upload and create reusable reference materials
- **Search Community References (搜索社区主体库)** — Search public reference library
- **Query task (查询任务)** — Check task status and retrieve results

---

## Setup

1. Install dependencies:
   ```bash
   cd scripts
   pip install -r requirements.txt
   ```
2. Obtain a VIDU token (e.g. from the official Vidu console).
3. Set environment variables:
   - `export VIDU_TOKEN="your-token"` (required / 必填)
   - `export VIDU_BASE_URL=https://service.vidu.cn` (mainland China / 国内, default / 默认) or `https://service.vidu.com` (overseas / 海外)
4. Verify installation:
   ```bash
   ./scripts/vidu-cli task submit --help
   ```

---

## Data usage and privacy note

**IMPORTANT**: This skill sends user-provided data to Vidu's servers:

- Text prompts → Vidu API
- Image bytes (uploaded files) → Vidu API servers (service.vidu.cn or service.vidu.com)
- Task parameters (settings, model version, etc.)

Before using this skill, confirm that sending your content to Vidu is acceptable for your privacy and intellectual property requirements. Data handling follows Vidu's official policy.

**Security recommendations**:

- Create a token with limited scope if possible
- Avoid using production/privileged tokens for initial testing
- Review Vidu's terms of service and privacy policy

**Vidu Terms & Privacy**:

- Overseas: https://www.vidu.com/terms
- Mainland China: https://www.vidu.cn/terms

---

## Overview

Vidu media generation is **asynchronous**: submit a task with `vidu-cli task submit` → get **task_id** → use `vidu-cli task get <task_id>` to query status/result when needed.

**Model version**

- **Q3** → `model_version: "3.2"`
- **Q2** → `model_version: "3.1"`
- **Q1** → `model_version: "3.0"`

- **text-to-image (文生图)**: Text only. Generate images from text prompts.
- **text-to-video (文生视频)**: Text only. Generate videos from text prompts.
- **image-to-video (图生视频)**: One image + text. Generate videos from an image with text description.
- **head-tail-image-to-video (首尾帧生视频)**: Two images (start frame, end frame) + text. Generate videos with start/end frame control.
- **reference-to-image (参考生图)**: Image + reference + text (text required, image + reference at most 7, at least one). Generate images using reference materials.
- **reference-to-video (参考生视频)**: Image + reference + text (text required, image + reference at most 7, at least one). Generate videos using reference materials.
- **Create References (创建主体)**: Upload images → preprocess → create element. Returns element `id` and `version`.
- **Search References (查询主体)**: `vidu-cli element list [--keyword kw]`. Returns personal elements.
- **Search Community References (搜索社区主体库)**: `vidu-cli element search --keyword "keyword"`. Returns community elements.

See **references/parameters.md** for all parameter constraints and valid values.

---

## Workflow: Submit → Query → Get media URL

**Summary**: Submit task with `vidu-cli task submit` → get `task_id` → Query with `vidu-cli task get <task_id>` → Get media URLs from response.

### 1. text-to-video (文生视频)

```bash
vidu-cli task submit \
  --type text2video \
  --prompt "A cat walks in the snow at sunset" \
  --duration 5 \
  --model-version 3.2 \
  --aspect-ratio 16:9 \
  --transition pro \
  --resolution 1080p
```

Response: `{"ok": true, "task_id": "3202402178822691"}`

### 2. text-to-image (文生图)

```bash
vidu-cli task submit \
  --type text2image \
  --prompt "A beautiful sunset over the ocean" \
  --duration 0 \
  --model-version 3.1 \
  --resolution 2k
```

### 3. image-to-video (图生视频)

```bash
vidu-cli upload /path/to/image.jpg
# Returns: {"ok": true, "upload_id": "123", "ssupload_uri": "ssupload:?id=123"}

vidu-cli task submit \
  --type img2video \
  --prompt "The cat starts running" \
  --image "ssupload:?id=123" \
  --duration 5 \
  --model-version 3.2
```

### 4. head-tail-image-to-video (首尾帧生视频)

```bash
vidu-cli upload start.jpg   # → ssupload:?id=111
vidu-cli upload end.jpg     # → ssupload:?id=222

vidu-cli task submit \
  --type headtailimg2video \
  --prompt "Smooth transition between scenes" \
  --image "ssupload:?id=111" \
  --image "ssupload:?id=222" \
  --duration 5 \
  --model-version 3.2
```

### 5. reference-to-video (参考生视频)

```bash
vidu-cli task submit \
  --type character2video \
  --prompt "[@aliya] walks in the garden" \
  --material "aliya:3073530415201165:1765430214" \
  --duration 5 \
  --model-version 3.2 \
  --aspect-ratio 16:9
```

### 6. reference-to-image (参考生图)

```bash
vidu-cli task submit \
  --type reference2image \
  --prompt "[@aliya] portrait in watercolor style" \
  --material "aliya:3073530415201165:1765430214" \
  --duration 0 \
  --model-version 3.1 \
  --resolution 2k
```

### 7. Query Task Result

```bash
vidu-cli task get $TASK_ID
```

- `state`: `success` | `failed` | `processing` | ...
- On **success**: `{"ok": true, "state": "success", "media_urls": ["https://..."]}`
- On **failed**: `{"ok": true, "state": "failed", "err_code": "...", "err_msg": "..."}` — note `ok: true`, task failure is in `state`
- On **processing**: `{"ok": true, "state": "processing"}` — no media_urls yet

### 8. Task Status SSE (optional)

```bash
vidu-cli task sse $TASK_ID
```

Streams SSE events directly to stdout. **Warning for Agents**: SSE streams continuous events which may produce large output.

### 9. Image Upload (图片上传)

```bash
vidu-cli upload /path/to/image.jpg
```

Returns: `{"ok": true, "upload_id": "123456", "ssupload_uri": "ssupload:?id=123456"}`

Use `ssupload_uri` in `--image` arguments.

---

## Create References (创建主体)

Upload 1–3 images, preprocess, then create element. Returns element `id` and `version` for use in reference tasks.

```bash
# Step 1: Upload images
vidu-cli upload image1.jpg   # → ssupload:?id=123

# Step 2: Preprocess
vidu-cli element preprocess \
  --name "my_character" \
  --image "ssupload:?id=123"
# Returns: {"ok": true, "id": "456", "recaption": {"description": "...", "style": "..."}}

# Step 3: Create
vidu-cli element create \
  --id "456" \
  --name "my_character" \
  --image "ssupload:?id=123" \
  --description "A young woman with long black hair"
# Returns: {"ok": true, "id": "789", "version": "1"}
```

---

## Search References (查询主体)

```bash
vidu-cli element list --keyword "关键词"
```

Returns: `{"ok": true, "elements": [{"id": "...", "version": "...", "name": "..."}], "next_page_token": "..."}`

---

## Search Community References (搜索社区主体库)

```bash
vidu-cli element search --keyword "老虎" --pagesz 20
```

Returns: `{"ok": true, "elements": [{"id": "...", "version": "...", "name": "...", "description": "...", "category": [...]}], "next_page_token": "..."}`

Present results as a list: `id`, `version`, `name`, `description`, `category`.

---

## Implementation Guide

1. **Determine task type**: text-to-image, text-to-video, image-to-video, head-tail-image-to-video, reference-to-image, reference-to-video, or Create References.
2. **Choose parameters**: See **references/parameters.md** for valid values per task type.
3. **Prepare inputs**: For image/reference tasks, upload image(s) via `vidu-cli upload <image_path>` to get `ssupload_uri`. For reference tasks, ensure elements exist (create if needed).
4. **Submit**: `vidu-cli task submit --type ... --prompt ... [options]`. Capture `task_id` from response.
5. **Query**: `vidu-cli task get <task_id>` until state is success/failed; on success return `media_urls`; on failure return err_code/err_msg.

---

## Prompt Tips

- **text-to-image (文生图)**: Describe the subject, style, lighting, and composition explicitly.
- **text-to-video (文生视频)**: Include scene and action; you can add camera direction (e.g. "镜头缓慢左移", "特写跟拍").
- **image-to-video (图生视频)**: Describe what motion or change happens in the scene.
- **head-tail-image-to-video (首尾帧)**: Similar start/end frames give smooth transition; very different frames can be used for morphing effects.
- **reference-to-video / reference-to-image**: Create the reference first; in the text prompt use references like `[@reference_name]`; ensure text is always present.

---

## Output to the user

- **After submit**: Return the **task_id**; tell the user the task is in progress.
- **After query**: If state is success, return the **media_urls**; if failed, report **err_code** and **err_msg** exactly.
- **On CLI error** (`ok: false`): Report the error `type`, `http_status`, `code`, and `message` exactly. **Never guess or infer the cause.**

---

## Bundled resources

- **references/parameters.md** — Task types and parameter constraints.
- **references/errors_and_retry.md** — Error handling and retry guidance.

---

## Fallback (no Python)

If the environment **cannot** run Python 3, execution via `vidu-cli` is not possible. Tell the user that this skill requires Python 3 with `requests` and `Pillow` packages, and point them to **references/parameters.md** for task parameter details.
