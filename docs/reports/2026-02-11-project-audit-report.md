# 📋 CTF-ASAS 功能实现状态全面审计报告 (2026-02-11)

## 一、总体路线图状态评估

| 版本 | Roadmap 标记 | 实际状态 | 评估 |
|:---|:---|:---|:---|
| **v1.0** | ✅ | ✅ 已完成 | MCP 协议、基础 Agent 解题闭环 |
| **v2.0** | ✅ | ⚠️ **部分完成** | 代码骨架在，但有关键空壳 |
| **v3.0** | ✅ | ⚠️ **空壳为主** | 架构搭好了，核心逻辑是 Mock |
| **v4.0** | ✅ | ⚠️ **空壳为主** | 代码结构在，但未对接真实工具 |
| **v4.5** | ⬜ | ⚠️ **空壳已写** | IDA Client/Tools 代码在，但完全未经实战验证 |
| **v5.0** | ⬜ | ❌ 未设计 | 无文档无代码 |

> ⚠️ **关键结论**：路线图中标记为 ✅ 的 v2.0~v4.0，实际上大量功能是空壳/Mock。真正“可用”的只有 v1.0 的基础链路。

---

## 二、核心功能差距分析 (Core Gaps)

### 🔴 1. 严重空壳模块 (Missing Core Logic)

* **v3.0 多 Agent 调度器 (`dispatcher.py`)**: 当前 `dispatch_to_agent` 仅为 Mock 实现，不会真正调用子代理，也未集成 `LLMFactory` 进行多模型映射。
* **CLI v1/v2 模式**: `__main__.py` 中的 `run_v1()` 和 `run_v2()` 函数体为 `pass`，只有 v3 模式有初步逻辑。
* **v4.0 反思机制 (Reflection Loop)**: 虽然代码中有定义，但由于底层工具调用是 Mock 且永远返回 success，反思节点从未经过实战触发与验证。

### 🟡 2. 功能不完整模块 (Partial Implementation)

* **v4.5 IDA Pro 集成**: 异步客户端 (`IdaClient`) 和工具包装器 (`ida_tools.py`) 已实现骨架，但尚未对接真实的 IDA MCP Server，且 `connect` 逻辑仍为 Mock。
* **高级 Crypto 能力**: 缺少 PRD 要求的所有现代密码学攻击（RSA 复杂攻击、AES padding oracle、ECC、格密码）及 SageMath 集成。
* **深度 Reverse 能力**: 缺少动态分析（GDB 自动化）、模拟执行（Unicorn/Qiling）及符号执行（Angr）。
* **v2.5 语义分析与 Solver 生成**: 设计文档已有规划，但 `nodes.py` 和 `workflow.py` 中缺失对应逻辑节点。

### 🟠 3. PRD 明确要求但完全缺失 (System Gaps)

* **F3.1.1 递归任务树**: 缺乏任务看板、子任务生成与状态回滚的多路径平衡能力。
* **F3.1.2 结构化事实仓库**: 缺乏带溯源的原子事实存储机制（Fact Store）。
* **F3.1.3 输出智能蒸馏**: 缺乏对长输出工具（如 Ghidra 反编译）的精华提取引擎。
* **F3.4.1 动态审批流**: 关键 Exploit 操作的人工确认流程尚未实现。
* **安全加固**: PRD 要求的 **gVisor (runsc)** 容器隔离尚未集成，当前仍使用普通 Docker。
* **人机交互**: 缺失 React 前端 Dashboard 与一键 Xterm.js 介入功能。

---

## 三、现有完成度清单 (Implemented)

| 模块 | 状态 | 核心实现 |
|:---|:---|:---|
| **MCP Server** | ✅ | FastMCP 框架，工具注册与分包完整 |
| **Kali VM** | ✅ | `vmrun` 驱动集成，支持 nmap, sqlmap, steghide 等 8 工具 |
| **Web 基础** | ✅ | 目录扫描、基础报错 SQLi 检测、链接提取 |
| **沙箱环境** | ✅ | `sandbox.py` 实现受限 Docker 容器执行 |
| **Ghidra** | ✅ | Headless Docker 化与基础反编译提取流程 |
| **记忆层** | ✅ | ChromaDB 向量库存取与基础 RAG 检索 (`retriever.py`) |
| **平台对接** | ✅ | CTFd API 适配器，支持查题与自动提交 |

---

## 四、后续建议任务优先级

### 第一优先级 (P0: 解开 Mock)

1. **真实分发**: 实现 `dispatch_to_agent` 的真实 LLM 调度，移除 Mock 逻辑。
2. **完善 CLI**: 补全 `run_v1` 和 `run_v2` 的执行与输出逻辑。
3. **串联 v4.5**: 使用真实 ida-pro-mcp 验证 `IdaClient` 链路。

### 第二优先级 (P1: 增强大脑)

4. **事实仓库**: 落实 `FactStore` 结构化存储，作为 Agent 间的上下文桥梁。
2. **回溯机制**: 在 `orchestrator` 中引入任务树管理，支持路径重试。
3. **SageMath 集成**: 部署 SageMath 容器并增加 Crypto 高级求解工具。

### 第三优先级 (P2: 系统化)

7. **gVisor 集成**: 提升沙箱安全性。
2. **前端 Dashboard**: 提供可视化任务树和人机协同接口。
