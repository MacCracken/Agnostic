FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agents/performance/ ./agents/performance/
COPY config/ ./config/
COPY shared/ ./shared/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV AGENT_ROLE=performance

# Run the performance agent
CMD ["python", "-m", "agents.performance.qa_performance"]