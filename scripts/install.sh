#!/bin/bash

# CTF-ASAS 一键安装脚本
# 灵感来自 Chaitin SafeLine

set -e

echo "🚀 正在开始 CTF-ASAS 安装程序..."

# 1. 环境检查
echo "🔍 检查运行环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo "📦 未找到 poetry，正在尝试自动安装..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# 2. 安装依赖
echo "🛠️ 正在安装项目依赖..."
poetry install

# 3. 环境变量配置
if [ ! -f .env ]; then
    echo "📝 创建 .env 模板..."
    echo "ANTHROPIC_API_KEY=your_key_here" > .env
    echo "💡 提示: 请稍后编辑 .env 文件配置您的 API Key"
fi

# 4. 构建可执行程序 (可选)
echo "🔨 正在构建自动化解题工具 (ctfbot)..."
poetry run PYTHONPATH=src pyinstaller --onefile --name ctfbot --paths src src/asas_agent/__main__.py --noconfirm

# 5. 完成安装
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CTF-ASAS 安装成功！"
echo ""
echo "📍 可执行程序位置: $(pwd)/dist/ctfbot"
echo "👉 您可以将其添加到 PATH: export PATH=\$PATH:$(pwd)/dist"
echo ""
echo "🚀 尝试运行: ./dist/ctfbot --help"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
