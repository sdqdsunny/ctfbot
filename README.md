# 🤖 CTF-ASAS (Automated Solving Agent System)

[![Version](https://img.shields.io/badge/version-0.7.0-orange.svg)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)
[![Next.js](https://img.shields.io/badge/UI-Next.js-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

<p align="center">
  <strong>🧠 多智能体协作 × 🎯 实时可视化 × 🐉 Kali 武器库 — 全自动 CTF 解题系统</strong>
</p>

CTF-ASAS 是一款基于大语言模型（LLM）多智能体协作的**全自动化 CTF 解题系统**。通过 **Model Context Protocol (MCP)** 将 AI 决策与底层安全工具解耦，配合**实时可视化命令中心 UI**，实现从"理解题意"到"工具利用"到"获取 Flag"的完整闭环。

> **核心亮点：** 不只是一个 AI 聊天包装器——它是一个拥有真实武器库的自动化渗透测试编排系统。

---

## ✨ 核心特性

### 🧠 多智能体架构 (Multi-Agent Orchestration)

- **ReAct Orchestrator**：基于 LangGraph 的编排器，自动规划攻击步骤、分配任务、汇总结果
- **专业子代理**：Web Agent (SQL注入/XSS)、Crypto Agent (加密分析)、Reverse Agent (逆向工程)、PWN Agent (漏洞利用)
- **智能路由**：URL 模式识别自动匹配攻击策略（如检测到 `sqli-labs/Less-1` → 直接调用 sqlmap）
- **Human-in-the-Loop**：危险操作（nmap/sqlmap/kali_exec）需用户审批后执行

### 🎯 实时可视化命令中心 (Command Center UI)

- **拓扑图**：实时展示 Orchestrator → Worker Agent → Tool 的调用链路和状态
- **Orchestrator Uplink**：实时流式展示 Agent 思考过程、工具调用请求、审批卡片
- **Step Inspector**：点击任意节点查看完整的 payload、执行日志和推理结论
- **多模型切换**：一键切换 DeepSeek R1 / GPT-4o / Claude 3.5

### 🐉 Kali Linux 武器库 (Tool Arsenal)

| 工具 | 能力 | 来源 |
|------|------|------|
| `kali_sqlmap` | SQL 注入自动检测与利用 | Kali VM |
| `kali_nmap` | 端口扫描与服务指纹识别 | Kali VM |
| `kali_dirsearch` | Web 目录与文件爆破 | Kali VM |
| `kali_exec` | 在 Kali 中执行任意命令 (hydra/steghide 等) | Kali VM |
| `kali_sqlmap` | SQL 注入自动检测与利用 | Kali VM |
| `reverse_ghidra` | Ghidra 无头反编译 → C 伪代码 | Docker |
| `reverse_angr` | Angr 符号执行求解约束 | Native |
| `crypto_decode` | Base64/Hex/Morse/ROT13 万能解码 | Native |
| `sandbox_execute` | Docker 沙箱内执行 Python/Shell | Docker |
| `vnc_capture_screen` | VNC 截屏实现 GUI 交互 (Computer Use) | VMware |

### 🔌 多 LLM 支持

- **DeepSeek R1 / Chat** — 推荐，性价比最高
- **Claude 3.5 Sonnet** — Anthropic
- **GPT-4o** — OpenAI
- **Gemini 2.5 Flash** — Google
- **智谱 GLM-4** — 国产大模型
- **LM Studio** — 本地部署大模型
- **Mock** — 无需 API Key 的测试模式

---

## 🏗️ 系统架构

```text
┌──────────────────────────────────────────────────────────┐
│                   ctfbot 命令中心 (Next.js)                │
│   ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│   │ 拓扑图    │  │ Orchestrator │  │  Step Inspector   │   │
│   │ (React   │  │   Uplink     │  │  (Payload/Logs)   │   │
│   │  Flow)   │  │ (实时日志)    │  │                   │   │
│   └──────────┘  └──────────────┘  └──────────────────┘   │
└────────────────────────┬─────────────────────────────────┘
                         │ WebSocket (ws://localhost:8765)
┌────────────────────────▼─────────────────────────────────┐
│              UI Server (FastAPI + Uvicorn)                 │
│   /api/analyze → spawn Agent    /api/events → broadcast   │
│   /api/approve → approval IPC   /ws → WebSocket hub       │
└────────────────────────┬─────────────────────────────────┘
                         │ subprocess + HTTP events
┌────────────────────────▼─────────────────────────────────┐
│           asas-agent (多智能体决策大脑)                      │
│   ┌──────────────────────────────────────────────┐       │
│   │  ReAct Orchestrator (LangGraph 状态机)         │       │
│   │  ├── Web Agent (SQL注入/XSS/目录扫描)          │       │
│   │  ├── Crypto Agent (加密分析)                   │       │
│   │  ├── Reverse Agent (Ghidra/Angr)              │       │
│   │  └── PWN Agent (漏洞利用)                      │       │
│   └──────────────────────────────────────────────┘       │
└────────────────────────┬─────────────────────────────────┘
                         │ Model Context Protocol (Stdio)
┌────────────────────────▼─────────────────────────────────┐
│           asas-core-mcp (能力引擎 / 工具服务器)             │
│  🐉 Kali Tools (sqlmap/nmap/hydra via vmrun)              │
│  🔬 Reverse (Ghidra Headless + Angr Symbolic)             │
│  🔐 Crypto (Base64/RSA/AES/Hash)                         │
│  🖥️ VNC (GUI Computer Use via asyncvnc)                   │
│  📦 Sandbox (Docker 隔离执行)                              │
│  🧠 Memory (ChromaDB RAG 知识库)                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 前置条件

- **Python 3.10+** & [Poetry](https://python-poetry.org/)
- **Node.js 18+** & pnpm (UI 界面)
- **Docker Desktop** (Ghidra/沙箱)
- **VMware Fusion/Workstation + Kali Linux VM** (渗透工具，可选)

### 1. 安装后端

```bash
git clone https://github.com/sdqdsunny/ctfbot.git
cd ctfbot
poetry install
```

### 2. 配置 API Key

```bash
# 创建 .env 文件
cat > .env << 'EOF'
DEEPSEEK_API_KEY=your_deepseek_key_here
# 可选：其他模型的 Key
# ANTHROPIC_API_KEY=your_claude_key
# GOOGLE_API_KEY=your_gemini_key
# OPENAI_API_KEY=your_openai_key
EOF
```

或者复制配置模板：

```bash
cp v3_deepseek.yaml.example v3_deepseek.yaml
# 编辑 v3_deepseek.yaml 填入你的 API Key
```

### 3. 启动 UI 界面

```bash
# 终端 1: 启动后端 API Server
poetry run python -m src.asas_agent.ui_server

# 终端 2: 启动前端 UI
cd ui && pnpm install && pnpm dev
```

打开浏览器访问 **<http://localhost:3000>** 🎉

### 4. 开始解题

1. 在顶部输入框粘贴目标 URL（如 `http://target:81/Less-1/`）
2. 选择 LLM 模型（推荐 DeepSeek R1）
3. 点击 **ANALYZE**
4. 观察 Agent 自动分析、调用工具、请求审批
5. 点击 **Approve** 授权执行危险操作
6. 查看实时日志和执行结果

### 5. CLI 模式 (无 UI)

```bash
# DeepSeek 模式 (v3 多智能体)
poetry run python -m src.asas_agent run --url "http://target:81/Less-1/" --llm deepseek --v3

# Mock 模式 (无需 API Key，验证流程)
poetry run python -m src.asas_agent run --llm mock --v3 "解码这段 Base64: SGVsbG8="

# Claude 模式
poetry run python -m src.asas_agent run --llm claude --v3 "扫描目标并识别漏洞"
```

---

## 📂 项目结构

```
ctfbot/
├── src/
│   ├── asas_agent/          # 🧠 Agent 决策层
│   │   ├── __main__.py      # CLI 入口 + 智能指令生成
│   │   ├── ui_server.py     # FastAPI WebSocket 服务器
│   │   ├── graph/           # LangGraph 编排 (workflow.py, dispatcher.py)
│   │   ├── agents/          # 专业子代理 (web.py, crypto.py, pwn.py...)
│   │   ├── llm/             # LLM 适配层 (DeepSeek/Claude/Gemini/LMStudio)
│   │   └── utils/           # UIEmitter 事件推送
│   └── asas_mcp/            # 🔧 MCP 工具服务器
│       ├── tools/           # 所有工具实现
│       │   ├── kali.py          # Kali VM 桥接 (vmrun)
│       │   ├── kali_sqlmap.py   # SQLMap 自动化
│       │   ├── reverse_ghidra.py # Ghidra 无头反编译
│       │   ├── reverse_angr.py  # Angr 符号执行
│       │   ├── crypto.py        # 加密工具
│       │   ├── sandbox.py       # Docker 沙箱
│       │   └── vnc_core.py      # VNC GUI 交互
│       └── server.py        # MCP Stdio 服务器入口
├── ui/                      # 🎨 Next.js 命令中心界面
│   └── src/
│       ├── components/      # React 组件
│       │   ├── CommandCenter.tsx     # 主界面
│       │   ├── ProcessGraph.tsx      # 拓扑图 (React Flow)
│       │   ├── OrchestratorChat.tsx  # 实时日志
│       │   └── PayloadInspector.tsx  # 步骤检查器
│       └── hooks/
│           ├── useAgentEvents.ts     # WebSocket 事件流
│           └── useGraphData.ts       # 事件→图数据转换
├── tests/                   # 测试套件
├── v3_deepseek.yaml.example # LLM 配置模板
└── pyproject.toml           # Poetry 依赖管理
```

---

## 🔐 安全声明

- **所有 API Key 仅通过环境变量加载**，代码中不含任何硬编码密钥
- 配置文件 (`v3_deepseek.yaml`, `.env`) 已加入 `.gitignore`
- 本工具**仅用于授权的安全评估和 CTF 竞赛**，严禁用于非法用途

---

## 📅 路线图

- [x] **v0.1 ~ v0.4**: 基础 Agent、MCP 工具链、RAG 记忆、Docker/Kali 集成
- [x] **v0.5**: 逆向引擎增强 (Angr/Ghidra/IDA Pro)
- [x] **v0.6**: 分布式 Swarm 架构 (Ray Cluster, GPU Scheduler)
- [x] **v0.7 (Current)**: **命令中心 UI** + 实时可视化 + 多模型支持 + 智能攻击策略
- [ ] **v0.8**: 真实靶场全自动化复现 (sqli-labs, DVWA, HackTheBox)
- [ ] **v0.9**: Agent 记忆增强 + 自动 Writeup 生成
- [ ] **v1.0**: 正式生产就绪版本

---

## 📄 开源协议

[Apache License 2.0](LICENSE)

---

<p align="center">
  <sub>Built with 🧠 AI + 🐉 Kali + ☕ Coffee</sub>
</p>
