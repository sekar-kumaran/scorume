# ==============================================================================
# Backend Dockerfile — Scorume
# Python 3.11-slim | Pre-caches spaCy & Sentence-Transformers for 100% Local Inference
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies required by PyMuPDF, psycopg2, and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --extra-index-url https://download.pytorch.org/whl/cpu torch --no-cache-dir && \
    pip install -r /app/requirements.txt && \
    python -m spacy download en_core_web_sm && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy backend application and sample_data (so /api/demo/load-sample works inside container)
COPY backend/app /app/app
COPY sample_data /sample_data

# Pre-generate the 12 real-profile PDF/DOCX resumes during image build
RUN python /sample_data/resumes/generate_synthetic_resumes.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
