# Flux v1.0 Quick Reference

## 🚀 Common Operations

### Start the Stack
```bash
docker compose up -d
```

### Check Logs
```bash
docker compose logs -f flux-api
docker compose logs -f flux-worker-io
```

### Restart Workers
```bash
docker compose restart flux-worker-io flux-worker-cpu
```

---

## 🔍 API Smoke Tests (v1)

### Hybrid Search
```bash
curl -X POST http://localhost:8000/api/v1/search \
     -H "Content-Type: application/json" \
     -d '{"query": "latest news on space exploration", "limit": 5}'
```

### Content Extraction
```bash
curl -X POST http://localhost:8000/api/v1/extract \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/some-article"}'
```

---

## 🧪 Testing & Quality

### Backend Tests
```bash
# Run all tests
PYTHONPATH=backend pytest backend/tests/ -v

# Filtered test run
PYTHONPATH=backend pytest backend/tests/test_routes.py -v
```

### Static Analysis (Mypy & Bandit)
```bash
# Type Checking
mypy backend/app --config-file=mypy.ini

# Security Scanning
bandit -r backend/app -v
```

---

## 🔒 Security Policy

Flux employs strict quality gates:
*   **Static Analysis**: Automated Bandit scans for injection risks.
*   **Dependency Audits**: Safety scans for known CVEs.
*   **Encrypted Secrets**: Keys are never hardcoded; managed via `.env`.

---

## 📊 Observability Links

| Service | Local URL |
| :--- | :--- |
| **API Endpoints** | http://localhost:8000/api/v1 |
| **Metrics** | http://localhost:8000/api/v1/metrics |
| **Grafana** | http://localhost:3000 |
| **Flower** | http://localhost:5555 |
