# REST API Reference

The REST API is powered by FastAPI and exposes full session management.

## Start the Server

```bash
pip install -e ".[api]"
python scripts/run_dev.py
```

The server starts on `http://localhost:8000` by default.

- **Interactive docs (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI schema:** `http://localhost:8000/openapi.json`

---

## Sessions

### Create a Session

**`POST /sessions`**

Creates a new generation session. Returns the session ID and initial status.

**Request body:**

```json
{
  "genre": "classic_rock",
  "key": "E",
  "mode": "minor",
  "tempo": 120,
  "sections": 4,
  "with_keys": false
}
```

| Field | Type | Default | Description |
| ----- | ---- | ------- | ----------- |
| `genre` | string | `"classic_rock"` | Genre preset |
| `key` | string | `"C"` | Root note (C–B) |
| `mode` | string | `"major"` | Scale mode |
| `tempo` | int | `120` | BPM (40–300) |
| `sections` | int | `4` | Number of song sections |
| `with_keys` | bool | `false` | Include keyboard agent |

**Response `201 Created`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-04-11T02:00:00Z"
}
```

---

### Run a Session

**`POST /sessions/{id}/run`**

Triggers track generation for the given session. This is synchronous — the response returns once all MIDI files have been written.

**Response `200 OK`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "files": [
    "output/550e8400_drums.mid",
    "output/550e8400_bass.mid",
    "output/550e8400_guitar.mid",
    "output/550e8400_full.mid"
  ]
}
```

---

### Get Session Status

**`GET /sessions/{id}`**

Returns the current session status and any generated file paths.

**Response `200 OK`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "genre": "classic_rock",
  "key": "E",
  "mode": "minor",
  "tempo": 120,
  "files": ["output/550e8400_full.mid"],
  "created_at": "2026-04-11T02:00:00Z",
  "completed_at": "2026-04-11T02:00:05Z"
}
```

---

## Tracks

### List Tracks

**`GET /sessions/{id}/tracks`**

Returns metadata about each generated track (instrument, MIDI channel, file path).

**Response `200 OK`:**

```json
[
  {"instrument": "drums",  "channel": 9,  "file": "output/550e8400_drums.mid"},
  {"instrument": "bass",   "channel": 1,  "file": "output/550e8400_bass.mid"},
  {"instrument": "guitar", "channel": 2,  "file": "output/550e8400_guitar.mid"}
]
```

---

## Export

### Download Combined MIDI

**`GET /sessions/{id}/export`**

Downloads the combined multi-track MIDI file as `application/octet-stream`.

```bash
curl -O http://localhost:8000/sessions/<id>/export
```

---

## Error Responses

| Status | Meaning |
| ------ | ------- |
| `400 Bad Request` | Invalid parameters (e.g. unknown genre or key) |
| `404 Not Found` | Session ID does not exist |
| `409 Conflict` | Session has already been run |
| `500 Internal Server Error` | Generation failure (check server logs) |

---

## cURL Examples

```bash
# Create
SESSION=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"genre":"blues","key":"A","mode":"minor","tempo":110}' \
  | jq -r '.id')

# Run
curl -X POST http://localhost:8000/sessions/$SESSION/run

# Download
curl -o backing-track.mid http://localhost:8000/sessions/$SESSION/export
```
