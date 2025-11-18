FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    git \
    bash \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install gsocket tools (gs-netcat, etc.)
# Using static binary releases for fast and reliable installation
RUN set -ex && \
    ARCH=$(uname -m) && \
    echo "Detected architecture: $ARCH" && \
    if [ "$ARCH" = "x86_64" ]; then \
        GSOCKET_URL="https://github.com/hackerschoice/gsocket/releases/download/v1.4.43/gsocket_1.4.43_linux-x86_64.tar.gz"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        GSOCKET_URL="https://github.com/hackerschoice/gsocket/releases/download/v1.4.43/gsocket_1.4.43_linux-aarch64.tar.gz"; \
    else \
        echo "ERROR: Unsupported architecture: $ARCH" >&2; \
        exit 1; \
    fi && \
    echo "Downloading gsocket from: $GSOCKET_URL" && \
    curl -fsSL --retry 3 --retry-delay 2 "$GSOCKET_URL" -o /tmp/gsocket.tar.gz && \
    echo "Download complete. Extracting..." && \
    mkdir -p /tmp/gsocket && \
    tar -xzf /tmp/gsocket.tar.gz -C /tmp/gsocket && \
    echo "Installing binaries..." && \
    find /tmp/gsocket -name 'gs-*' -type f -exec mv {} /usr/local/bin/ \; && \
    chmod +x /usr/local/bin/gs-* && \
    rm -rf /tmp/gsocket* && \
    echo "Verifying installation..." && \
    which gs-netcat && gs-netcat -h | head -5 && \
    echo "gsocket installation successful"

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Copy and set entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
