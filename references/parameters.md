# Vidu Task Parameters Reference

## Task Support Matrix

| Task Type | CLI Command | Model Version | Duration | Resolution | Aspect Ratio | Transition | Notes |
|-----------|-------------|---------------|----------|------------|--------------|-----------|-------|
| text-to-image | `vidu-cli task submit` type: text2image | 3.1, 3.2_fast_m, 3.2_pro_m | 0 | 1080p, 2k, 4k | 4:3, 3:4, 1:1, 9:16, 16:9 | N/A | - |
| text-to-video | `vidu-cli task submit` type: text2video | 3.0, 3.1, 3.2 | 3.0: 5s; 3.1: 2-8s; 3.2: 1-16s | 1080p | 16:9, 9:16, 1:1, 4:3, 3:4 | 3.2: pro/speed; 3.0/3.1: N/A | - |
| image-to-video | `vidu-cli upload` + `vidu-cli task submit` type: img2video | 3.0, 3.1, 3.2 | 3.0: 5s; 3.1: 2-8s; 3.2: 1-16s | 1080p | From image (don't pass) | 3.0: creative/stable; 3.1/3.2: pro/speed | 1 image + text |
| head-tail-image-to-video | `vidu-cli upload` (2x) + `vidu-cli task submit` type: headtailimg2video | 3.0, 3.1, 3.2 | 3.0: 5s; 3.1: 2-8s; 3.2: 1-16s | 1080p | N/A | 3.0: creative/stable; 3.1/3.2: pro/speed | 2 images + text |
| reference-to-image | `vidu-cli element search` + `vidu-cli task submit` type: reference2image | 3.1, 3.2_fast_m, 3.2_pro_m | 0 | 1080p, 2k, 4k | 4:3, 3:4, 1:1, 9:16, 16:9 | N/A | image+reference ≤7 |
| reference-to-video | `vidu-cli element search` + `vidu-cli task submit` type: character2video | 3.0, 3.1, 3.1_pro, 3.2 | 3.0: 5s; 3.1: 2-8s; 3.1_pro: -1/2-8s; 3.2: 1-16s | 1080p | 16:9, 9:16, 1:1, 4:3, 3:4 | N/A | image+reference ≤7 |

---

## CLI Commands

### Upload Image
```bash
vidu-cli upload <image_path>
```
- Auto-detects image dimensions
- Compresses if > 10MB
- Returns: `upload_id`, `ssupload_uri`

### Submit Task
```bash
vidu-cli task submit \
  --type <task_type> \
  --prompt "text prompt" \
  [--image "ssupload:?id=..."]  \
  [--material "name:id:version"] \
  --duration <seconds> \
  --model-version <version> \
  [--aspect-ratio <ratio>] \
  [--transition <mode>] \
  [--resolution <res>] \
  [--sample-count <n>] \
  [--codec <codec>] \
  [--movement-amplitude <amp>] \
  [--schedule-mode <mode>]
```

`--image` and `--material` can be specified multiple times.

### Query Task
```bash
vidu-cli task get <task_id>
```
- Returns: `state` (created/queueing/processing/success/failed), `media_urls` (if success), `err_code`/`err_msg` (if failed)

### Stream Task Status (SSE)
```bash
vidu-cli task sse <task_id>
```

### Search Community References
```bash
vidu-cli element search --keyword "keyword" [--pagesz 20]
```

### Create Reference
```bash
vidu-cli upload image1.jpg
# → {"ok": true, "ssupload_uri": "ssupload:?id=123"}

vidu-cli element preprocess \
  --name "my_character" \
  --image "ssupload:?id=123"

vidu-cli element create \
  --id "<id_from_preprocess>" \
  --name "my_character" \
  --image "ssupload:?id=123" \
  --description "description text"
```

---

## Input Parameters

### type (required)
- `text2image` — Text to image
- `text2video` — Text to video
- `img2video` — Image to video
- `headtailimg2video` — Head-tail frames to video
- `reference2image` — Reference to image
- `character2video` — Reference to video

### input.prompts (required, array)
- **Text prompt**: `{"type": "text", "content": "<string>"}` (max 4096 chars)
- **Image prompt**: `{"type": "image", "content": "ssupload:?id=<upload_id>"}`

Order for headtailimg2video: [text, image1, image2]
Order for reference tasks: text required; image + material combined ≤7

### input.enhance (required)
- Must be `true` (enables recaption)

### input.editor_mode (optional)
- Default: `"normal"`

---

## Settings Parameters

### model_version (required)
- `3.0` — Q1
- `3.1` — Q2 (text2image, reference2image, 2-8s videos)
- `3.2` — Q3 (1-16s videos)
- `3.1_pro` — Q2 pro (character2video only)
- `3.2_fast_m` — Q3 fast mode (text2image/reference2image only, 2k/4k)
- `3.2_pro_m` — Q3 pro mode (text2image/reference2image only, 2k/4k)

### duration (required for video, 0 for image)
- text2image: `0`
- text2video/img2video/headtailimg2video/character2video:
  - 3.0/3.2: 1-16 seconds
  - 3.1: 2-8 seconds
- reference2image: `0`

### resolution (optional, default 1080p)
- text2image: `1080p` (3.1), `2k`/`4k` (3.2_fast_m)
- reference2image: `1080p`, `2k`, `4k`
- video tasks: `1080p` only

### aspect_ratio (optional, task-dependent)
- text2image/reference2image: `4:3`, `3:4`, `1:1`, `9:16`, `16:9`
- text2video/character2video: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`
- img2video: **don't pass** (derived from image)
- headtailimg2video: **don't pass**

### transition (optional, video only)
- text2video (3.0/3.2): `pro` (cinematic), `speed` (fast)
- text2video (3.1): **don't pass**
- img2video/headtailimg2video: `pro`, `speed`
- reference tasks: **don't pass**

### Other settings
- `sample_count`: 1 (default)
- `schedule_mode`: `normal` (default)
- `codec`: `h265` (default)
- `use_trial`: `true`/`false`
- `movement_amplitude`: `auto` (optional)

---

## Error Handling

All CLI commands return structured JSON:

**Success:**
```json
{"ok": true, "task_id": "...", ...}
```

**Failure:**
```json
{"ok": false, "error": {"type": "client_error|http_error|network_error", "message": "...", "http_status": 422, "code": "invalid_param"}}
```

**Never guess error causes** — read the `error` object exactly as returned.

---

## Validation Rules

- `type` must be valid task type
- `model_version` must support the task type
- `duration` must be in valid range for model + task
- `resolution` must be supported by task type
- `aspect_ratio` must not be passed for img2video/headtailimg2video
- `transition` must not be passed for reference tasks or text2image
- `enhance` must be `true`
- Image + reference count ≤ 7 for reference tasks
