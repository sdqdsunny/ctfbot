FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml ./

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-nmap \
    mcp

# 复制源代码
COPY src/ ./src/

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app/src

# 启动命令
CMD ["python", "-m", "uvicorn", "asas_mcp.server:create_app", "--host", "0.0.0.0", "--port", "8000"]
