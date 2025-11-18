FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    bash \
    make \
    autoconf \
    automake \
    libtool \
    openssl \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install gsocket tools (gs-netcat, etc.)
# Building from source for reliable Docker installation
RUN cd /tmp && \
    git clone https://github.com/hackerschoice/gsocket.git && \
    cd gsocket && \
    ./bootstrap && \
    ./configure && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/gsocket && \
    # Verify installation
    ldconfig && \
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
