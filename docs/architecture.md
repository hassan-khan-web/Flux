# Architecture Deep Dive

Flux is built as a high-throughput **Acquisition Engine**. It uses an asynchronous, multi-phase pipeline to transform raw web data into AI-ready knowledge.

---

## 🏗️ System Overview

Flux follows a **Distributed Service Architecture**:

*   **API Layer**: FastAPI handles routing, validation, and request queuing.
*   **Task Broker**: Redis manages the communication between the API and the worker cluster.
*   **Worker Pool**: 
    *   `scrapers` queue: Handles I/O-heavy operations (requests, browser automation).
    *   `embeddings` queue: Handles CPU-heavy operations (vectorization, scoring).
*   **Storage Layer**: PostgreSQL stores structured results and pgvector embeddings. Redis provides an LRU cache for high-speed retrieval of repeated queries.

---

## ⚡ The Phase-Chain Pipeline

When a search is triggered, the system executes a chained sequence of Celery tasks:

### Phase 1: Acquisition & Extraction
*   **Service**: `ScraperService` + `ParserService`
*   **Process**: 
    1.  Fetch organic results or scrape a single URL.
    2.  Extract primary text using heuristic-based BeautifulSoup and semantic-aware Trafilatura.
    3.  Identify and isolate crucial metadata like **Author** and **Publication Date**.

### Phase 2: Enrichment & Polishing
*   **Service**: `LLMJudgeService` (OpenRouter)
*   **Process**: 
    1.  Parallel deep-scraping of top-tier results.
    2.  "AI Final Polish": Sending extracted text to a specialized LLM prompt to remove residual web artifacts (e.g., "Click here," "Sign up now") and normalize the tone.

### Phase 3: Semantic Layer
*   **Service**: `ChunkerService` + `EmbeddingsService`
*   **Process**: 
    1.  Recursively split polished text into overlapping chunks.
    2.  Generate vector embeddings for all chunks.
    3.  Execute **Semantic Deduplication** to remove redundant results.

### Phase 4: Validation & Scoring
*   **Service**: `LLMJudgeService`
*   **Process**:
    1.  The entire knowledge package is evaluated for **Relevance** (alignment with query) and **Credibility** (source authority).
    2.  Final results are written to the database and indexed.

---

## 🛡️ Resilience & Scaling

*   **Provider Fallbacks**: If a primary scraper is rate-limited, the system automatically cycles through healthy fallbacks.
*   **Horizontal Scaling**: Workers can be scaled independently of the API. To handle more scrape volume, simply increase the `worker-io` count.
*   **Observability**: Full Prometheus/Grafana integration allows you to monitor Latency, Throughput, and Provider Health in real-time.
