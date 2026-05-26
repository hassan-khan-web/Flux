FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for building wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ML models
COPY scripts/download_models.py ./scripts/
RUN python ./scripts/download_models.py

COPY . .


# Environment variables
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
