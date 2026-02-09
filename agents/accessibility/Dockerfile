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

# Copy agent code
COPY agents/accessibility/ ./agents/accessibility/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV AGENT_ROLE=accessibility

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Expose port for health checks
EXPOSE 8006

# Run the Accessibility Tester agent
CMD ["python", "-m", "agents.accessibility.qa_accessibility"]
