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
COPY ./agents/security_compliance/qa_security_compliance.py /app/qa_security_compliance.py

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "qa_security_compliance.py"]