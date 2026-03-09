# DevVerse — Docker Container
# ─────────────────────────────────────────────────────────────
# Runs the full DevVerse Streamlit app with all agents, RAG, & SHAP.
#
# Build:  docker build -t devverse .
# Run:    docker run -p 8501:8501 --env-file .env devverse
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps for sentence-transformers, torch, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Ensure outputs directory exists
RUN mkdir -p outputs generated_project chroma_db

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Disable Streamlit telemetry and CrewAI telemetry
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV CREWAI_DISABLE_TELEMETRY=true

# Run Streamlit
CMD ["streamlit", "run", "DevVerse.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
