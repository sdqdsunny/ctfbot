#!/bin/bash
set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting ASAS Core MCP Server (Stdio Mode)..." >&2

# 激活虚拟环境
source "$PROJECT_ROOT/.venv/bin/activate"

# 设置 PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# 启动 MCP Server
exec python -m asas_mcp
