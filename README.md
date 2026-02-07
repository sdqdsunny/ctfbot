# CTF-ASAS (Capture The Flag - Automated Solving Agent System)

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)

CTF-ASAS 是一款基于大语言模型（LLM）多智能体协作的自动化 CTF（Capture The Flag）解题系统。它利用 **Model Context Protocol (MCP)** 协议，将复杂解题意图与底层专业工具解耦，旨在实现从“题目理解”到“Flag 获取”的全自动化闭环。

## 🌟 核心特性

- **Agent-Native 架构**: 基于 LangGraph 构建任务编排层，模拟安全专家的逻辑闭环（理解 -> 规划 -> 执行 -> 总结）。
- **工具链解耦 (MCP)**: 所有底层能力（扫描、编码、逆向、取证）均作为标准 MCP Tool 调用。
- **混合题型支持**: 已实现对 Crypto, Recon, Reverse, Misc 基础题型的覆盖。
- **本地记忆层 (RAG)**: 集成 ChromaDB 知识库，支持解题技巧、WP 片段的存取与检索。
- **隔离沙箱**:（规划中）所有 Payload 执行均在 gVisor 隔离容器中完成。

## 🏗️ 系统架构

```text
┌─────────────────────────────────────┐
│   用户接口 (CLI / Web Dashboard)     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   asas-agent (决策大脑)              │
│   - LangGraph 状态机                 │
│   - LLM 提供者 (Claude/Mock)         │
│   - 任务规划与反思                   │
└──────────────┬──────────────────────┘
               │ Model Context Protocol (Stdio)
┌──────────────▼──────────────────────┐
│   asas-core-mcp (能力引擎)            │
│  - 🛠️ Recon: 端口扫描、指纹探测       │
│  - 🔐 Crypto: 万能解码、RSA/AES 求解  │
│  - 📂 Misc/Reverse: 文件识别、字符串提取│
│  - 🧠 Memory: ChromaDB 知识存取       │
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 一键安装 (推荐)

如果您在 Linux 或 macOS 环境下，可以使用以下脚本快速完成环境配置、依赖安装及工具构建：

```bash
# 执行本地安装脚本
bash scripts/install.sh
```

> **注**: 生产环境下可将其托管至服务器，实现 `curl -fsSL ... | bash` 的体验。

### 2. 手动安装 (Poetry)

确保已安装 [Python 3.10+](https://www.python.org/) 和 [Poetry](https://python-poetry.org/)。

### 2. 配置环境变量

如果需要使用 Claude 3.5 真实 LLM，请在目录下创建 `.env` 文件：

```env
ANTHROPIC_API_KEY=your_sk_key_here
```

### 3. 运行程序

#### 模式 A：Mock 模式（无需 API Key，验证流程用）

```bash
python -m src.asas_agent "解码这段 Base64: SGVsbG8gQVNBUw=="
```

#### 模式 B：Claude 模式（需配置 API Key）

```bash
python -m src.asas_agent --llm claude "请扫描目标 IP 192.168.1.1 并识别开放服务"
```

## 🛠️ 可用工具清单 (MCP Tools)

| 工具名称 | 功能描述 | 题型 |
| --- | --- | --- |
| `recon_scan` | 多端口网络扫描与服务探测 | Recon |
| `crypto_decode` | Base64/Hex/URL 等格式自动识别与解码 | Crypto |
| `misc_identify_file` | 文件头识别与 Meta 数据分析 | Misc |
| `reverse_extract_strings` | 二进制文件敏感字符串提取 | Reverse |
| `memory_add/query` | RAG 记忆层：存储解题事实或检索知识点 | Core |

## 📅 路线图 (Roadmap)

- [x] **v1.0 (MVP)**: MCP 协议打通，基础 Agent 解题闭环，RAG 集成。
- [ ] **v1.5**: 对接 BUUCTF/CTFd 平台 API，实现全自动取题与 Flag 提交。
- [ ] **v2.0**: 集成 Ghidra/SageMath Server，支持深度逆向与复杂密码学计算。
- [ ] **v3.0**: 引入递归任务树 (Task Tree)，支持复杂多步 Web 渗透任务。

## 📄 开源协议

MIT License
