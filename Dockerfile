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
# Download static binaries directly from GitHub releases
RUN set -ex && \
    ARCH=$(uname -m) && \
    echo "Detected architecture: $ARCH" && \
    if [ "$ARCH" = "x86_64" ]; then \
        GSOCKET_BINARY="gs-netcat_linux-x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        GSOCKET_BINARY="gs-netcat_linux-aarch64"; \
    else \
        echo "ERROR: Unsupported architecture: $ARCH" >&2; \
        exit 1; \
    fi && \
    GSOCKET_URL="https://github.com/hackerschoice/gsocket/releases/download/v1.4.43/${GSOCKET_BINARY}" && \
    echo "Downloading gsocket from: $GSOCKET_URL" && \
    curl -fsSL --retry 3 --retry-delay 2 "$GSOCKET_URL" -o /usr/local/bin/gs-netcat && \
    chmod +x /usr/local/bin/gs-netcat && \
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
