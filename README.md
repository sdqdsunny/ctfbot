# 🤖 CTF-ASAS (Automated Solving Agent System)

[![Version](https://img.shields.io/badge/version-0.8.0-orange.svg)](pyproject.toml)
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
- **7 个专业子代理**，按题型自动派遣：

  | 子代理 | 职责 |
  |--------|------|
  | `web` | SQL 注入 / XSS / 目录爆破 |
  | `crypto` | 编码识别 / 古典与现代密码分析 |
  | `reverse` | Ghidra 反编译 / angr 符号执行 / IDA |
  | `pwn` | 栈溢出利用 / 模糊测试 / ROP |
  | `recon` | 端口扫描 / 服务指纹识别 |
  | `writeup` | 历年大赛 WriteUp 检索 |
  | `memory` | 知识库读写与沉淀 |

- **智能路由**：URL 模式识别自动匹配攻击策略（如检测到 `sqli-labs/Less-1` → 直接调用 sqlmap）
- **Human-in-the-Loop**：危险操作（nmap/sqlmap/kali_exec）需用户审批后执行
- **🚩 Flag 验证闭环**：不轻信模型的自述。**L1** 用统一的 `FlagExtractor` 对工具输出做格式校验，
  命中即进入 `flag_capture` 节点；**L2** 在连续未命中时按三种场景（执行报错 / 有进展 / 长期停滞）
  生成反思提示，引导模型换策略而不是重复失败动作

### 🎯 实时可视化命令中心 (Command Center UI)

- **拓扑图**：实时展示 Orchestrator → Worker Agent → Tool 的调用链路和状态
- **Orchestrator Uplink**：实时流式展示 Agent 思考过程、工具调用请求、审批卡片
- **Step Inspector**：点击任意节点查看完整的 payload、执行日志和推理结论
- **多模型切换**：一键切换 DeepSeek R1 / GPT-4o / Claude 3.5

### 🐉 Kali Linux 武器库 (Tool Arsenal)

MCP 工具服务器共注册 **36 个工具**，下表为常用项：

| 工具 | 能力 | 来源 |
|------|------|------|
| `kali_sqlmap` | SQL 注入自动检测与利用 | Kali VM |
| `kali_nmap` | 端口扫描与服务指纹识别 | Kali VM |
| `kali_dirsearch` | Web 目录与文件爆破 | Kali VM |
| `kali_exec` | 在 Kali 中执行任意命令 (hydra/steghide 等) | Kali VM |
| `kali_upload_file` / `kali_file` / `kali_checksec` | 文件投递与二进制侦察 | Kali VM |
| `kali_binwalk` / `kali_foremost` / `kali_steghide` / `kali_zsteg` / `kali_tshark` | 隐写与流量分析 | Kali VM |
| `reverse_ghidra_decompile` | Ghidra 无头反编译 → C 伪代码 | Docker |
| `ghidra_list_functions` / `ghidra_decompile_function` | 函数清单 / 单函数精反编译 | Docker |
| `crypto_decode` | Base64/Hex/Morse/ROT13 万能解码 | Native |
| `sandbox_execute` | Docker 沙箱内执行 Python/Shell | Docker |
| `vnc_capture_screen` | VNC 截屏实现 GUI 交互 (Computer Use) | VMware |
| `memory_query` / `memory_add` | 知识库语义检索与写入 | ChromaDB |
| `search_writeups` | 历年 WP 全文检索 | SQLite FTS5 |
| `list_ctf_scripts` / `run_ctf_script` | 解题脚本检索与沙箱执行 | Docker |
| `platform_get_challenge` / `platform_submit_flag` | CTF 平台取题与提交 | HTTP |

> **另有一组工具不走 MCP**：angr 符号执行（`reverse_angr_solve` / `reverse_angr_eval`）、
> pwn 模糊测试（`pwn_fuzz_start` / `pwn_fuzz_check` / `pwn_fuzz_triage`）、
> horde 种子桥接（`pwn_horde_*`）、GPU 爆破（`gpu_hashcat_crack` / `gpu_status`）、
> IDA 远程调用（`ida_*`）、以及 pwn 工具（`kali_pwn_cyclic` / `kali_pwn_gdb`）。
> 这些是子代理直接持有的原生 LangChain 工具，按需在 `agents/reverse.py` 等处装配。

### 📚 CTF 知识库 (Knowledge Base)

| 层级 | 内容 | 检索方式 | MCP 工具 | 交付方式 |
|------|------|----------|----------|----------|
| **核心知识** | 19 篇专题 (含 Payload 速查表)，698 chunks | ChromaDB 语义检索 | `memory_query` | 随仓库交付 (1.0MB) |
| **大赛 WP** | 1041 篇历年 WriteUp (强网杯/HITCON/西湖论剑等) | SQLite FTS5 全文检索 | `search_writeups` | 需拉取 (约 35MB) |
| **解题脚本** | 47 个工具集 (RSA/CRC32/USB流量/盲水印等) | 分类注册 + 沙箱执行 | `list_ctf_scripts` / `run_ctf_script` | 需拉取 (4.4MB) |

> 数据来源：[Dest1ny-Sec/Des-CTF-Knowledge](https://github.com/Dest1ny-Sec/Des-CTF-Knowledge) (MIT)
>
> **大件语料不随仓库分发**（体积 + 第三方汇编），首次使用需拉取一次：
>
> ```bash
> python scripts/fetch_corpus.py     # 克隆上游并建链 + 建 WP 索引（约 70MB，一次性）
> python scripts/fetch_corpus.py --check   # 随时自检语料与索引是否齐备
> ```
>
> 核心知识库的逐文件来源与授权见 [`data/knowledge_base/LICENSE`](data/knowledge_base/LICENSE)。
>
> 知识库为空时加载器会**直接报错退出**——CTF 场景下，自信的错答比明确失败更危险。

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
│   │  ├── PWN Agent (漏洞利用)                      │       │
│   │  ├── Recon Agent (侦察)                        │       │
│   │  ├── WriteUp Agent (历年题解检索)               │       │
│   │  └── Memory Agent (知识库读写)                  │       │
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

### 2. 创建配置文件

本仓库**不含 `v3_config.yaml`** —— 它是本地配置，已被 `.gitignore` 忽略。
首次使用需从模板创建，否则启动会报 `Configuration file not found`：

```bash
cp v3_config.yaml.example v3_config.yaml
```

> **API Key 不写在这个文件里。** 配置中的 `provider` 字段决定读哪个环境变量
> （`deepseek` → `DEEPSEEK_API_KEY`，见 `src/asas_agent/llm/factory.py`）。
> 把 Key 直接写进 YAML 会导致它随文件被误提交。

需要切换 provider 时，用 `--config` 指定其它模板：

```bash
cp v3_lmstudio.yaml.example v3_lmstudio.yaml    # 本地模型
python -m src.asas_agent run --v3 --config v3_lmstudio.yaml "<目标>"
```

### 3. 配置 API Key

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

### 4. 拉取知识库语料（一次性）

核心知识库 19 篇随仓库交付，开箱即用。WP 全文与脚本工具合计约 40MB，
为第三方汇编，不随仓库分发，需拉取一次：

```bash
python scripts/fetch_corpus.py
```

随时自检语料与索引是否齐备：

```bash
python scripts/fetch_corpus.py --check
```

### 5. 启动 UI 界面

```bash
# 终端 1: 启动后端 API Server
poetry run python -m src.asas_agent.ui_server

# 终端 2: 启动前端 UI
cd ui && pnpm install && pnpm dev
```

打开浏览器访问 **<http://localhost:3000>** 🎉

### 6. 开始解题

1. 在顶部输入框粘贴目标 URL（如 `http://target:81/Less-1/`）
2. 选择 LLM 模型（推荐 DeepSeek R1）
3. 点击 **ANALYZE**
4. 观察 Agent 自动分析、调用工具、请求审批
5. 点击 **Approve** 授权执行危险操作
6. 查看实时日志和执行结果

### 7. CLI 模式 (无 UI)

```bash
# DeepSeek 模式 (v3 多智能体)
poetry run python -m src.asas_agent run --url "http://target:81/Less-1/" --llm deepseek --v3

# Mock 模式 (无需 API Key，验证流程)
# 注意：mock 用子串匹配识别意图（大小写不敏感），关键词只有这几组——
#   fetch / get challenge → 取题      decode → 解码      submit → 提交
#   scan / explore / analyze / 探查 / pwn → 派发子 agent
# 其它说法不会触发任何工具：包括"分析一下"这类中文描述（中文只认字面的"探查"），
# 以及只给一个 URL 而不带上述关键词的写法。
poetry run python -m src.asas_agent run --llm mock --v3 "scan the target 127.0.0.1"

# Claude 模式
poetry run python -m src.asas_agent run --llm claude --v3 "扫描目标并识别漏洞"
```

**退出码**（便于脚本与 CI 判断结果）：

| 码 | 含义 |
|----|------|
| `0` | 任务完成且捕获到 flag |
| `1` | 运行期间出错 |
| `2` | 无法启动（配置文件缺失、未提供目标） |
| `3` | 任务跑完但未捕获到 flag |

---

## 📂 项目结构

```
ctfbot/
├── src/
│   ├── asas_agent/          # 🧠 Agent 决策层
│   │   ├── __main__.py      # CLI 入口 + 智能指令生成
│   │   ├── ui_server.py     # FastAPI WebSocket 服务器
│   │   ├── graph/           # LangGraph 编排 (workflow.py, dispatcher.py, verifier.py)
│   │   ├── agents/          # 专业子代理 (web/crypto/reverse/pwn/recon/writeup/memory)
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
├── scripts/
│   └── fetch_corpus.py      # 大件语料拉取 + WP 索引构建
├── tests/                   # 测试套件
├── v3_config.yaml.example   # LLM 配置模板
└── pyproject.toml           # Poetry 依赖管理
```

---

## 🔐 安全声明

- **所有 API Key 仅通过环境变量加载**，代码中不含任何硬编码密钥
- 本地配置与密钥文件（`.env`、`v3_*.yaml`）已加入 `.gitignore`；
  仓库中只保留 `*.yaml.example` 模板
- 本工具**仅用于授权的安全评估和 CTF 竞赛**，严禁用于非法用途

---

## 📅 路线图

- [x] **v0.1 ~ v0.4**: 基础 Agent、MCP 工具链、RAG 记忆、Docker/Kali 集成
- [x] **v0.5**: 逆向引擎增强 (Angr/Ghidra/IDA Pro)
- [x] **v0.6**: 分布式 Swarm 架构 (Ray Cluster, GPU Scheduler)
- [x] **v0.7**: **命令中心 UI** + 实时可视化 + 多模型支持 + 智能攻击策略
- [x] **v0.8 (Current)**: **CTF 知识库整合** (19篇核心知识 + 1041篇WP + 47个脚本工具)
- [ ] **v0.9**: 真实靶场全自动化复现 (sqli-labs, DVWA, HackTheBox)
- [ ] **v1.0**: Agent 记忆增强 + 自动 Writeup 生成
- [ ] **v1.1**: 正式生产就绪版本

---

## 📄 开源协议

[Apache License 2.0](LICENSE)

---

<p align="center">
  <sub>Built with 🧠 AI + 🐉 Kali + ☕ Coffee</sub>
</p>
