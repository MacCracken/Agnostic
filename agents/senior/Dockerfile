FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including OpenCV and other computer vision libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for senior QA
RUN pip install --no-cache-dir \
    opencv-python \
    scikit-learn \
    pandas \
    numpy \
    playwright

# Install Playwright browsers
RUN playwright install chromium

# Copy agent code
COPY agents/senior/ ./agents/senior/
COPY advanced_testing/ ./advanced_testing/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV AGENT_ROLE=senior

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port for health checks
EXPOSE 8002

# Run the Senior QA agent
CMD ["python", "-m", "agents.senior.senior_qa"]