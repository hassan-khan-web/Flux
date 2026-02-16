# Flux v1.0: Autonomous Knowledge Acquisition Engine

Flux is a standalone, model-agnostic knowledge acquisition API designed for modern AI systems that require fresh, structured, and AI-ready information from the web. It solves the "Cold Start" problem in RAG systems by providing a production-ready infrastructure for real-time acquisition, cleaning, and structuring of high-quality knowledge.

Flux focuses exclusively on the acquisition layer—delivering clean, enriched documents that can be directly consumed by any embedding pipeline, vector database, or LLM without architectural lock-in.

---

## 🏗️ Project File Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI Routes & Pydantic Schemas
│   │   │   ├── routes.py       # Versioned v1 Endpoints
│   │   │   └── schemas.py      # Request/Response Definitions
│   │   ├── db/                 # PostgreSQL & pgvector Integration
│   │   │   ├── database.py     # Connection Handling
│   │   │   ├── models.py       # SQLAlchemy Models
│   │   │   └── repository.py   # Data Access Layer
│   │   ├── services/           # Core Logic Services
│   │   │   ├── chunker.py      # Recursive Text Partitioning
│   │   │   ├── embeddings.py   # Vector Generation
│   │   │   ├── formatter.py    # Deduplication & Markdown Gen
│   │   │   ├── llm_judge.py    # AI Scoring & Polish (OpenRouter)
│   │   │   ├── parser.py       # HTML Noise Removal & Meta Extraction
│   │   │   └── scraper.py      # Hybrid Search & Headless Scraping
│   │   ├── static/             # Frontend Assets (Production Build)
│   │   ├── utils/              # Shared Utilities (Logging, Cache)
│   │   └── worker.py           # Celery Task Definitions (IO/CPU)
│   ├── main.py                 # FastAPI Application Root
│   ├── requirements.txt        # Python Dependencies
│   ├── Dockerfile              # Backend Containerization
│   └── tests/                  # Comprehensive Pytest Suite
├── frontend/
│   ├── src/                    # TypeScript Source
│   │   ├── main.ts             # UI Logic & API Interaction
│   │   ├── style.css           # Modern Vanilla CSS Aesthetics
│   │   └── marked.js           # Markdown Rendering
│   ├── index.html              # Main Entry Point
│   ├── vite.config.ts          # Build Configuration
│   └── Dockerfile              # Frontend Containerization
├── docs/                       # Structured Technical Documentation
│   ├── architecture.md         # Multi-Phase Pipeline Details
│   ├── api_reference.md        # Endpoint Documentation
│   └── deployment.md           # Docker & Environment Guide
├── scripts/                    # Maintenance & Evaluation Scripts
├── docker-compose.yml          # Infrastructure Orchestration
├── prometheus.yml              # Observability Configuration
├── insomnia_collection.json    # API Testing Collection
└── LICENSE                     # MIT License
```

---

## ⚡ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                KNOWLEDGE ACQUISITION REQUEST                                │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          FLUX API                                           │
│                                    (Orchestration Layer)                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                   QUERY HYDRATION                                   │   │
│   │  ┌──────────────────────────┐    ┌──────────────────────────────────────────────┐   │   │
│   │  │ Cache Check              │    │ Parameter Normalization                      │   │   │
│   │  │ (Redis LRU)              │    │ (Region, Language, Limit)                    │   │   │
│   │  └──────────────────────────┘    └──────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                              │
│                                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                  CANDIDATE SOURCES                                  │   │
│   │         ┌─────────────────────────────┐    ┌────────────────────────────────┐       │   │
│   │         │        HYBRID SEARCH        │    │        DEEP SCRAPE             │       │   │
│   │         │    (In-Network Results)     │    │     (Out-of-Network Data)      │       │   │
│   │         │                             │    │                                │       │   │
│   │         │  API-based retrieval        │    │  Headless browser sessions     │       │   │
│   │         │  (Tavily / Serp API)        │    │  bypassing web protection      │       │   │
│   │         └─────────────────────────────┘    └────────────────────────────────┘       │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                              │
│                                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                               EXOTIC EXTRACTION                                     │   │
│   │  Fetch additional data: author info, publish dates, full-text markdown cleaning.    │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                              │
│                                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                      FILTERING                                      │   │
│   │  Remove: duplicates, SEO noise, navigation elements, ads, and boilerplate content.  │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                              │
│                                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                       SCORING                                       │   │
│   │  ┌──────────────────────────┐                                                       │   │
│   │  │  AI Final Polish         │    LLM-based evaluation predicts:                     │   │
│   │  │  (Noise Removal)         │    Relevance, Source Credibility, Fact Density...     │   │
│   │  └──────────────────────────┘                                                       │   │
│   │               │                                                                     │   │
│   │               ▼                                                                     │   │
│   │  ┌──────────────────────────┐                                                       │   │
│   │  │  Weighted Scorer         │    Weighted Score = Σ (weight × Metrics)              │   │
│   │  │  (Relevance Reasoning)   │                                                       │   │
│   │  └──────────────────────────┘                                                       │   │
│   │               │                                                                     │   │
│   │               ▼                                                                     │   │
│   │  ┌──────────────────────────┐                                                       │   │
│   │  │  Semantic Chunker        │    Recursive character-splitting for                  │   │
│   │  │  (RAG Readiness)         │    overlapping context preservation                   │   │
│   │  └──────────────────────────┘                                                       │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                              │
│                                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                      SELECTION                                      │   │
│   │                    Sort by final score, select top K candidates                     │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                              │
│                                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              FILTERING (Post-Selection)                             │   │
│   │                 Final sanity checks (content safety / deduplication)                │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    STRUCTURED KNOWLEDGE                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend & Infrastructure
*   **FastAPI**: High-performance, asynchronous Python web framework.
*   **Celery + Redis**: Distributed task queue for non-blocking IO and heavy CPU tasks.
*   **PostgreSQL + pgvector**: Scalable storage for structured knowledge and vector embeddings.
*   **OpenRouter**: Model-agnostic LLM orchestration (Llama 3, Gemini, DeepSeek).
*   **Trafilatura & BeautifulSoup**: Advanced web parsing and boilerplate removal.

### Frontend
*   **Vite + TypeScript**: Modern build pipeline for a fast, type-safe interactive UI.
*   **Vanilla CSS**: Premium "Glassmorphism" aesthetics with smooth animations.

### Observability & DevOps
*   **Prometheus & Grafana**: Real-time metrics and health monitoring dashboards.
*   **Docker Compose**: Single-command orchestration for the entire 9-service stack.
*   **Flower**: Real-time Celery worker monitoring.

---

## 📖 Documentation

For detailed guides, please visit the [docs/](docs/INDEX.md) folder:
*   [Quick Start](docs/deployment.md)
*   [API Reference](docs/api_reference.md)
*   [Architecture Deep Dive](docs/architecture.md)
