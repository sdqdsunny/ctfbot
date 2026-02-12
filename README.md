# CTFBOT (Capture The Flag - Automated Solving Agent System)

[![Version](https://img.shields.io/badge/version-0.6.0-orange.svg)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)
[![Ray](https://img.shields.io/badge/Distributed-Ray-blue.svg)](https://docs.ray.io/)

CTFBOT 是一款基于大语言模型（LLM）多智能体协作的自动化 CTF（Capture The Flag）解题系统。它利用 **Model Context Protocol (MCP)** 协议，将复杂解题意图与底层专业工具解耦，并支持 **Ray 分布式集群 (Swarm)**，实现从“题目理解”到“Fuzzing/爆破”的全自动化闭环。

> **⚠️ Alpha Preview**: 当前版本 **v0.6.0** 为分布式架构预览版，核心功能完备但 API 可能发生变化。

## 🌟 核心特性 (v0.6.0 Swarm Edition)

- **🧠 智能体集群 (Swarm Fabric)**: 基于 Ray 的分布式架构，支持本地/远程节点混合组网，具备能力自动发现与信誉评分机制。
- **🐝 协同 Fuzzing (Synergic Fuzzing)**: 支持分布式 AFL++ 并行 Fuzzing，具备全局种子同步 (Seed Sync) 与 **Angr 符号执行破局** 能力。
- **💥 弹性 GPU 调度 (Elastic GPU)**: 实现了支持优先级抢占 (Preemption) 和故障漂移 (Failover) 的分布式 Hashcat 任务调度。
- **Agent-Native 架构**: 基于 LangGraph 构建任务编排层，模拟安全专家的逻辑闭环。
- **深度逆向**: 集成 Ghidra/Angr/IDA Pro (Headless)，支持全量伪代码提取与求解。
- **Kali Linux 虚拟机直连**: 通过 `vmrun` 驱动桥接 Kali VM，支持专业级安全工具链。

... (保留原有架构图与安装说明) ...

## 📅 路线图 (Roadmap)

我们正在对版本号进行标准化，当前处于 **v0.6.0 (Alpha)** 阶段。

- [x] **v0.1 ~ v0.4**: 基础 Agent、MCP 工具链、RAG 记忆、Docker/Kali 集成。
- [x] **v0.5**: 逆向引擎增强 (Angr/Ghidra)。
- [x] **v0.6.0 (Current)**: **分布式 Swarm 架构** (Ray Cluster, Fuzzing Synergy, GPU Scheduler)。
- [ ] **v0.7.x**: 稳定性增强、错误处理与日志优化 (Coming Soon)。
- [ ] **v0.8.x**: 真实靶场 (Real-World CTF) 复现与调优。
- [ ] **v1.0.0**: 正式生产就绪版本。

## 📄 开源协议

Apache License 2.0

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
│  - 🔐 Crypto: 万能解码、RSA 求解      │
│  - 📂 Misc/Reverse: 文件识别、Ghidra  │
│  - 🐉 Kali: sqlmap, nmap, steghide   │
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

### 3. 环境准备 (Environment Setup)

本项目采用 **"Agent-Native"** 架构，将核心逻辑与重型工具链解耦。为了获得完整体验，请确保满足以下环境要求：

#### 🔧 1. Docker 环境 (必须)

用于运行安全沙箱 (Sandbox) 及 Ghidra 反编译服务。

- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows) 或 Docker Engine (Linux)。
- 确保 docker 服务已启动。

#### 🐉 2. Kali Linux 虚拟机 (强烈推荐)

用于提供专业的渗透测试工具链 (sqlmap, nmap, steghide 等)。

- **虚拟化软件**: [VMware Fusion](https://www.vmware.com/products/fusion.html) (macOS) 或 Workstation (Windows/Linux)。
- **Kali 镜像**: 下载 [Kali Linux VMware Image](https://www.kali.org/get-kali/#kali-virtual-machines)。
- **配置要求**:
  - 用户名/密码: `kali` / `kali` (默认)。
  - 确保虚拟机处于 **运行状态**。
  - **macOS 用户**: 需要确保 `vmrun` 命令可用 (通常在 `/Applications/VMware Fusion.app/Contents/Library/vmrun`)。

> **注意**: 如果没有配置 Kali VM，涉及渗透测试的 MCP Tool 将不可用，但通用解密与逻辑分析功能不受影响。

### 4. 运行程序

#### 方式 A：Docker 容器运行 (推荐 - 快速体验)

我们提供了预构建的 Docker 镜像配置，方便快速拉起 Agent 环境。

1. **构建镜像**

   ```bash
   docker build -t ctfbot .
   ```

2. **运行容器**

   ```bash
   # 基础运行（仅限 Mock 模式）
   docker run --rm -it ctfbot "解码 SGVsbG8="

   # 完整功能（挂载 Docker Socket 以支持沙箱，配置 API Key）
   docker run --rm -it \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -e ANTHROPIC_API_KEY=your_key_here \
     ctfbot --llm claude "分析这个 Base64: ..."
   ```

   > **⚠️ 限制**: Docker 容器内无法直接调用宿主机的 VMware `vmrun`，因此 **Kali 工具链在 Docker 模式下不可用**。如需使用 Kali 工具，请使用源码运行或本地可执行文件。

#### 方式 B：源码运行 (全功能)

1. **安装依赖**

   ```bash
   poetry install
   ```

2. **配置环境变量**
   创建 `.env` 文件：

   ```env
   ANTHROPIC_API_KEY=your_sk_key_here
   # 可选：自定义 vmrun 路径
   # KALI_VMRUN_PATH=/path/to/vmrun
   ```

3. **启动 Agent**

   ```bash
   # Mock 模式
   python -m src.asas_agent "题目指令"

   # Claude 模式
   python -m src.asas_agent --llm claude "题目指令"
   ```

#### 模式 A：Mock 模式（无需 API Key，验证流程用）

```bash
python -m src.asas_agent "解码这段 Base64: SGVsbG8gQVNBUw=="
```

#### 模式 B：Claude 模式（需配置 API Key）

```bash
python -m src.asas_agent --llm claude "请扫描目标 IP 192.168.1.1 并识别开放服务"
```

| 工具名称 | 功能描述 | 来源 |
| --- | --- | --- |
| `recon_scan` | 多端口网络扫描与服务探测 | Native |
| `kali_sqlmap` | 自动化的 SQL 注入探测与利用 | Kali VM |
| `kali_steghide` | 隐写图像分析与数据提取 | Kali VM |
| `reverse_ghidra` | 自动化反编译二进制文件为 C 伪代码 | Docker |
| `crypto_decode` | Base64/Hex/Morse 等万能解码 | Native |
| `memory_query` | RAG 记忆层：检索解题技巧与历史事实 | ChromaDB |
