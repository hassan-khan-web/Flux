# Flux v1 API Reference

All endpoints are prefixed with `/api/v1`.

---

## 🔍 Core Endpoints

### `POST /api/v1/search`
The primary entry point for hybrid knowledge acquisition. Performs search, scraping, cleaning, and scoring.

**Request Body:**
```json
{
  "query": "Future of AI in 2026",
  "limit": 10,
  "mode": "search",
  "output_format": "markdown"
}
```

*   `mode`: `"search"` (Standard) or `"scrape"` (Direct URL acquisition).
*   `output_format`: `"markdown"` (Polished text) or `"json"` (Structured data).

**Return:** `202 status` with a `task_id`. Use this ID to poll the task status.

---

### `POST /api/v1/extract`
A low-latency endpoint for extracting core content from a specific URL without deep scraping.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "mode": "extract"
}
```

---

### `POST /api/v1/deep_scrape`
Triggers a headless session to bypass protection and extract high-fidelity knowledge from a specific URL.

**Request Body:**
```json
{
  "url": "https://example.com/protected-page",
  "mode": "scrape"
}
```

---

### `POST /api/v1/chunk`
A utility endpoint for segmenting raw text into manageable pieces for RAG.

**Request Body:**
```json
{
  "text": "Your long text here...",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Response:**
```json
{
  "chunks": ["chunk 1...", "chunk 2..."],
  "count": 2
}
```

---

## 🚦 Monitoring & Status

### `GET /api/v1/tasks/{task_id}`
Retrieves the result of a background acquisition task.

**Response States:**
*   `pending`: Task is in the queue.
*   `started`: Worker is currently processing.
*   `completed`: Result ready in the `result` field.
*   `failed`: Error details in the `error` field.

### `GET /api/v1/health`
Returns system health and provider connectivity status.

### `GET /api/v1/metrics`
Exposes Prometheus metrics for throughput, latency, and token usage.
