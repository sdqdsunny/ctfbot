# ASAS Core MCP - Phase 3: MCP Protocol Integration & Docker Setup

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有工具集成到真实的 MCP 协议中，并准备 Docker 容器化基础设施。

**Architecture:**

- 使用官方 MCP Python SDK
- 实现标准 MCP Server 与 Tools 注册
- 准备 Docker 基础镜像（为后续 gVisor 集成做准备）

**Tech Stack:** Python 3.10+, MCP SDK, Docker

---

### Task 9: 安装并集成 MCP SDK

**Files:**

- Modify: `pyproject.toml`
- Modify: `src/asas_mcp/server.py`
- Create: `tests/test_mcp_integration.py`

**Step 1: 更新依赖配置**

**pyproject.toml** (修改 dependencies 部分)

```toml
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.100.0"
uvicorn = "^0.20.0"
python-nmap = "^0.7.1"
mcp = "^1.0.0"  # 使用真实的 MCP SDK
```

**Step 2: 安装新依赖**

Run: `source .venv/bin/activate && pip install mcp`
Expected: 成功安装

**Step 3: 编写 MCP 集成测试**

**tests/test_mcp_integration.py**

```python
from asas_mcp.server import create_mcp_server

def test_mcp_server_has_tools():
    """测试 MCP Server 是否正确注册了工具"""
    server = create_mcp_server()
    tools = server.list_tools()
    
    # 验证核心工具已注册
    tool_names = [t.name for t in tools]
    assert "recon_scan" in tool_names
    assert "crypto_decode" in tool_names
    assert "misc_identify_file" in tool_names
    assert "reverse_extract_strings" in tool_names
```

**Step 4: 运行测试验证失败**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/test_mcp_integration.py -v`
Expected: FAIL (函数不存在)

**Step 5: 实现 MCP Server**

**src/asas_mcp/server.py** (重写)

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import Any
from .tools import recon, crypto, misc, reverse

def create_mcp_server() -> Server:
    """创建并配置 MCP Server"""
    server = Server("asas-core-mcp")
    
    # 注册 recon 工具
    @server.list_tools()
    async def list_tools_handler():
        return [
            Tool(
                name="recon_scan",
                description="执行网络侦察扫描",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "ports": {"type": "string", "default": "1-1000"}
                    },
                    "required": ["target"]
                }
            ),
            Tool(
                name="crypto_decode",
                description="解码常见编码格式",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "method": {"type": "string", "enum": ["base64", "hex", "url", "auto"]}
                    },
                    "required": ["content"]
                }
            ),
            Tool(
                name="misc_identify_file",
                description="识别文件类型",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Base64 编码的文件数据"}
                    },
                    "required": ["data"]
                }
            ),
            Tool(
                name="reverse_extract_strings",
                description="从二进制数据提取字符串",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Base64 编码的二进制数据"},
                        "min_length": {"type": "integer", "default": 4}
                    },
                    "required": ["data"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool_handler(name: str, arguments: dict) -> list[TextContent]:
        if name == "recon_scan":
            result = recon.scan(**arguments)
            return [TextContent(type="text", text=str(result))]
        elif name == "crypto_decode":
            result = crypto.decode(**arguments)
            return [TextContent(type="text", text=result)]
        elif name == "misc_identify_file":
            import base64
            data = base64.b64decode(arguments["data"])
            result = misc.identify_file_type(data)
            return [TextContent(type="text", text=str(result))]
        elif name == "reverse_extract_strings":
            import base64
            data = base64.b64decode(arguments["data"])
            result = reverse.extract_strings(data, arguments.get("min_length", 4))
            return [TextContent(type="text", text=str(result))]
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    return server

# 保留 FastAPI 版本用于 HTTP 访问
def create_app():
    from fastapi import FastAPI
    app = FastAPI(title="ASAS Core MCP")
    return app
```

**Step 6: 运行测试验证通过**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/test_mcp_integration.py -v`
Expected: PASS

**Step 7: 提交**

```bash
git add pyproject.toml src/asas_mcp/server.py tests/test_mcp_integration.py
git commit -m "feat: 集成 MCP SDK 并注册工具"
git push origin main
```

---

### Task 10: 创建 Dockerfile

**Files:**

- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `docker-compose.yml`

**Step 1: 创建 .dockerignore**

**.dockerignore**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.git/
*.md
docs/
tests/
.DS_Store
```

**Step 2: 创建 Dockerfile**

**Dockerfile**

```dockerfile
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
```

**Step 3: 创建 docker-compose.yml**

**docker-compose.yml**

```yaml
version: '3.8'

services:
  asas-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./src:/app/src:ro
    restart: unless-stopped
```

**Step 4: 构建 Docker 镜像**

Run: `docker build -t asas-core-mcp:latest .`
Expected: 成功构建

**Step 5: 测试容器运行**

Run: `docker run -d -p 8000:8000 --name asas-test asas-core-mcp:latest`
Expected: 容器启动成功

**Step 6: 验证容器健康**

Run: `curl http://localhost:8000/docs`
Expected: 返回 FastAPI 文档页面

**Step 7: 清理测试容器**

Run: `docker stop asas-test && docker rm asas-test`

**Step 8: 提交**

```bash
git add Dockerfile .dockerignore docker-compose.yml
git commit -m "feat: 添加 Docker 容器化支持"
git push origin main
```

---

### Task 11: 添加 MCP Server 启动脚本

**Files:**

- Create: `src/asas_mcp/__main__.py`
- Create: `scripts/start_mcp_server.sh`

**Step 1: 创建 Python 入口点**

**src/asas_mcp/**main**.py**

```python
import asyncio
from mcp.server.stdio import stdio_server
from .server import create_mcp_server

async def main():
    """MCP Server 主入口"""
    server = create_mcp_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: 创建启动脚本**

**scripts/start_mcp_server.sh**

```bash
#!/bin/bash
set -e

echo "Starting ASAS Core MCP Server..."

# 激活虚拟环境
source .venv/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# 启动 MCP Server
python -m asas_mcp
```

**Step 3: 赋予执行权限**

Run: `chmod +x scripts/start_mcp_server.sh`

**Step 4: 测试启动脚本**

Run: `./scripts/start_mcp_server.sh &`
Expected: Server 启动（后台运行）

**Step 5: 提交**

```bash
git add src/asas_mcp/__main__.py scripts/start_mcp_server.sh
git commit -m "feat: 添加 MCP Server 启动脚本"
git push origin main
```
