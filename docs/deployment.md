# Deployment & Environment Guide

Flux is designed to be deployed as a containerized stack using Docker Compose.

---

## 🚀 One-Command Deployment

From the project root, run:

```bash
docker compose up -d
```

This will initialize all 9 services:
1.  **flux-api**: The FastAPI entry point.
2.  **flux-worker-io**: Celery worker for search and scraping.
3.  **flux-worker-cpu**: Celery worker for embeddings, chunking, and LLM scoring.
4.  **flux-db**: PostgreSQL with pgvector.
5.  **flux-redis**: Broker and cache.
6.  **flux-flower**: Worker monitoring (available at `:5555`).
7.  **flux-prometheus**: Metrics collection.
8.  **flux-grafana**: Metrics visualization (available at `:3000`).
9.  **flux-frontend**: The interactive UI.

---

## 🔑 Environment Variables

Create a `.env` file in the project root with the following:

### Core Infrastructure
*   `REDIS_URL`: `redis://redis:6379/0`
*   `DATABASE_URL`: `db+postgresql://user:password@db:5432/flux_db`

### AI & Search Providers
*   `OPENROUTER_API_KEY`: Your OpenRouter key (for Scoring/Polish).
*   `TAVILY_API_KEY`: Your Tavily search key.
*   `SCRAPINGBEE_API_KEY`: (Optional) For headless scraping.

### Rate Limiting
*   `RATE_LIMIT_TIMES`: Max requests per period (e.g., `5`).
*   `RATE_LIMIT_SECONDS`: Time period in seconds (e.g., `60`).

---

## 📊 Observability

*   **API Metrics**: Access `http://localhost:8000/metrics`.
*   **Grafana Dashboards**: Access `http://localhost:3000` (Default: admin/admin) to view throughput and latency trends.
*   **Worker Status**: Access `http://localhost:5555` to see Celery task progress and success rates.
