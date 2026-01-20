FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

# Essential tools for Antigravity handshake and Python 3.14 compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    curl \
    procps \
    git \
    build-essential \
    gfortran \
    libssl-dev \
    libffi-dev \
    libsqlite3-dev \
    libopenblas-dev \
    liblapack-dev \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Global binary)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Python 3.14 via uv
RUN uv python install 3.14

# Create the user and ensure they own the workspace
RUN useradd -m vscode -s /bin/bash \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/apt/sudoers

USER vscode
WORKDIR /workspace