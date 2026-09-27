# stage 1: builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install poetry and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
# 与 CI（.github/workflows/*.yml 的 POETRY_VERSION）钉同一版本，
# 避免"CI 绿了但镜像里装的是另一套"。
ENV POETRY_VERSION=2.3.2
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
# poetry.lock 已随仓库提交，必须与 pyproject.toml 一起 COPY：
# poetry 只有在 lock 存在时才按 lock 装依赖，否则会退回现场解析——
# 那样两次构建就可能装到不同版本。这两个文件是成对的，改动也总是一起改。
COPY pyproject.toml poetry.lock ./

# Install dependencies via poetry
# optimized for caching: no dev deps, no interaction
# lock 与 pyproject 不一致时 poetry 会直接报错退出——这正是想要的：
# 构建失败好过悄悄装出一套没人验证过的依赖。
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

# 核心知识库 19 篇（随仓库交付，MIT，来源见该目录 LICENSE）
# agent 的记忆层依赖它；缺失时 load_initial_knowledge() 会直接抛错，
# 这是有意设计——空知识库会让 agent 在没有依据的情况下作答。
# 向量索引（chroma_db）不随镜像分发，会在容器内首次使用 memory 工具时自动构建。
COPY data/knowledge_base ./data/knowledge_base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Create a non-root user for security (optional but good practice)
# However, if we need docker socket access, we might need root or docker group.
# For now, running as root inside container is simpler for Docker-in-Docker scenarios (binding sock).

# Entrypoint to run the agent
ENTRYPOINT ["python", "-m", "src.asas_agent"]
CMD ["--help"]
