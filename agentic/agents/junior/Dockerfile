FROM python:3.11-slim

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

# Install additional dependencies for junior QA
RUN pip install --no-cache-dir \
    faker \
    pytest \
    pytest-playwright \
    scikit-learn \
    pandas \
    numpy \
    playwright

# Install Playwright browsers
RUN playwright install chromium

# Copy agent code
COPY agents/junior/ ./agents/junior/
COPY examples/ ./examples/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV AGENT_ROLE=junior

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Expose port for health checks
EXPOSE 8003

# Run the Junior QA agent
CMD ["python", "-m", "agents.junior.junior_qa"]