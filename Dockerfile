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
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        GSOCKET_URL="https://github.com/hackerschoice/gsocket/releases/latest/download/gsocket_1.4.43_linux-x86_64.tar.gz"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        GSOCKET_URL="https://github.com/hackerschoice/gsocket/releases/latest/download/gsocket_1.4.43_linux-aarch64.tar.gz"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -fsSL "$GSOCKET_URL" -o /tmp/gsocket.tar.gz && \
    tar -xzf /tmp/gsocket.tar.gz -C /tmp && \
    mv /tmp/gsocket_*_linux-*/bin/* /usr/local/bin/ && \
    chmod +x /usr/local/bin/gs-* && \
    rm -rf /tmp/gsocket* && \
    # Verify installation
    which gs-netcat && \
    gs-netcat -h | head -5

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
