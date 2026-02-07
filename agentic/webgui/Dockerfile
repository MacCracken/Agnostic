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

# Copy web GUI code
COPY webgui/ ./webgui/
COPY agents/ ./agents/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV CHAINLIT_HOST=0.0.0.0
ENV CHAINLIT_PORT=8000
ENV CHAINLIT_SERVER_ROOT=/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the web GUI
CMD ["chainlit", "run", "webgui/app.py", "--host", "0.0.0.0", "--port", "8000"]