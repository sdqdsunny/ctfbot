# stage 1: builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install poetry and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies via poetry
# optimized for caching: no dev deps, no interaction
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

# stage 2: runner
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
# nmap: required for recon tools
# netcat: useful for debugging and simple network tasks
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python modifications from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY src ./src
COPY .env.example .env

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Create a non-root user for security (optional but good practice)
# However, if we need docker socket access, we might need root or docker group.
# For now, running as root inside container is simpler for Docker-in-Docker scenarios (binding sock).

# Entrypoint to run the agent
ENTRYPOINT ["python", "-m", "src.asas_agent"]
CMD ["--help"]
