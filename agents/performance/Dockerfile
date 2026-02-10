FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY ./agents/performance/qa_performance.py /app/qa_performance.py

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "qa_performance.py"]