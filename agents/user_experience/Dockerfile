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
COPY ./agents/user_experience/qa_user_experience.py /app/qa_user_experience.py

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "qa_user_experience.py"]