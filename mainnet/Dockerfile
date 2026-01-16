# GSC Coin Mainnet Node Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data/.gsccoin

# Set environment variables
ENV PYTHONPATH=/app
ENV GSC_DATA_DIR=/data/.gsccoin
ENV GSC_NETWORK=mainnet

# Expose ports
EXPOSE 8333 8334 8335 9090

# Create non-root user
RUN useradd -m -u 1000 gscnode && \
    chown -R gscnode:gscnode /app /data
USER gscnode

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8335/api/v1/info', timeout=5)"

# Default command
CMD ["python", "-m", "mainnet.mainnet_node"]
