# Vidu API Reference (CLI Model)

This document describes the Vidu API endpoints. For CLI usage, see **parameters.md**.

## Base URL

- Mainland China (default): `https://service.vidu.cn`
- Overseas: `https://service.vidu.com`

Set via environment variable: `export VIDU_BASE_URL=https://service.vidu.cn`

---

## Authentication

All API requests require:
- `Authorization: Token {VIDU_TOKEN}`
- `Content-Type: application/json`
- `User-Agent: viduclawbot/1.0 (+{VIDU_BASE_URL})`

The `vidu-cli` tool handles these headers automatically.

---

## API Endpoints

### File Upload

**POST** `/tools/v1/files/uploads` — Create upload session
- Request: `{"metadata": {"image-width": "...", "image-height": "..."}, "scene": "vidu"}`
- Response: `{"id": ..., "put_url": "...", "expires_at": "..."}`

**PUT** `{put_url}` — Upload image bytes
- Headers: `Content-Type: image/jpeg`, `x-amz-meta-image-width`, `x-amz-meta-image-height`
- Response: ETag header

**PUT** `/tools/v1/files/uploads/{id}/finish` — Finalize upload
- Request: `{"etag": "...", "id": "..."}`
- Response: `{"uri": "ssupload:?id=..."}`

Use `vidu-cli upload <image_path>` to handle all three steps automatically.

---

### Task Management

**POST** `/vidu/v1/tasks` — Submit task
- Request: `{"type": "...", "input": {...}, "settings": {...}}`
- Response: `{"id": "task_id", ...}`

Use `vidu-cli task submit --type ... --prompt ... [options]` to submit.

**GET** `/vidu/v1/tasks/{task_id}` — Get task result
- Response: `{"state": "success|failed|...", "creations": [...], "err_code": "...", "err_msg": "..."}`

Use `vidu-cli task get <task_id>` to query.

**GET** `/vidu/v1/tasks/state?id={task_id}` — Stream task state (SSE)
- Response: Server-Sent Events stream with `state`, `estimated_time_left`, `err_code`, `queue_wait_time`

Use `vidu-cli task sse <task_id>` to stream.

---

### Material Elements (References)

**POST** `/vidu/v1/material/elements/pre-process` — Pre-process element
- Request: `{"components": [...], "name": "...", "type": "user"}`
- Response: `{"id": "...", "recaption": {"description": "...", "style": "..."}}`

Use `vidu-cli element preprocess --name ... --image ...`.

**POST** `/vidu/v1/material/elements` — Create element
- Request: `{"id": "...", "name": "...", "modality": "image", "type": "user", "components": [...], "version": "0", "recaption": {...}}`
- Response: `{"id": "...", "version": "..."}`

Use `vidu-cli element create --id ... --name ... --image ... --description ...`.

**GET** `/vidu/v1/material/elements/personal` — List personal elements
- Query: `pager.page`, `pager.pagesz`, `keyword`, `modalities`
- Response: `{"elements": [...], "next_page_token": "..."}`

Use `vidu-cli element list [--keyword kw]`.

**GET** `/vidu/v1/material/share_elements/feed` — Search community elements
- Query: `keyword`, `pager.page_token`, `pager.pagesz`, `modalities`, `sort_by`
- Response: `{"share_elements": [...], "next_page_token": "..."}`

Use `vidu-cli element search --keyword "keyword"`.

---

## Error Handling

All errors are returned as structured JSON by `vidu-cli`:

```json
{"ok": false, "error": {"type": "http_error|network_error|client_error", "message": "...", "http_status": 422, "code": "invalid_param"}}
```

**Never guess error causes** — read the `error` object exactly as returned.

See **errors_and_retry.md** for retry strategies.
