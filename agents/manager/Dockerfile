FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agents/manager/ ./agents/manager/
COPY config/ ./config/

# Create logs directory with proper permissions
RUN mkdir -p logs && chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app
ENV AGENT_ROLE=manager

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Expose port for health checks
EXPOSE 8001

# Run the QA Manager agent
CMD ["python", "-m", "agents.manager.qa_manager"]