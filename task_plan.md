# Task Plan: CLI Recovery & Fact Store Enhancement

<!-- 
  内容：这是你整个任务的路线图。将其视为你的“磁盘工作记忆”。
  原因：在进行 50 次以上的工具调用后，你可能会忘记最初的目标。此文件可保持目标的新鲜感。
  时间：首先创建此文件，然后再开始任何工作。每个阶段完成后进行更新。
-->

## 目标 (Goal)
<!-- 一句话描述你想要实现的目标 -->
补全 CLI (v1/v2) 基础功能，并增强子 Agent 与 Orchestrator 之间的结构化事实共享机制 (Fact Store)。

## 阶段 1：CLI 功能恢复 (Option A)

- [x] 实现 `run_v2()` 的思考过程与工具调用输出逻辑
- [x] 实现 `run_v1()` 的传统链式工作流逻辑
- [x] 验证 `ctfbot --v1` 和 `ctfbot --v2` 命令的可用性
- **状态：** complete

## 阶段 2：结构化事实仓库设计与实现 (Option B)

- [x] 头脑风暴：定义 `FactStore` 的数据结构 (已确定为分类结构化 B 方案)
- [x] 在 `AgentState` 中更新 `fact_store` 字段 (`src/asas_agent/graph/state.py`)
- [x] 修改 `AgentResult` 以包含 `extracted_facts` (`src/asas_agent/graph/dispatcher.py`)
- [x] 更新 `dispatcher.py` 中的解析逻辑，实现事实的自动合并 (Merge logic)
- [x] 更新各子代理（Crypto, Web, Recon）的系统提示词，引导其主动汇报事实
- [x] 更新 Orchestrator 工作流，实现事实到 Context 的动态注入
- **状态：** complete

## 阶段 3：集成测试与验证

- [x] 编写测试脚本模拟多步解题中的事实传递 (已完成 `test_fact_store.py`)
- [x] 验证跨 Agent 的事实共享行为 (已通过 Mock 流程模拟 Port 81 发现验证)
- **状态：** complete

## 阶段 4：本地大模型集成与增强

- [x] 配置本地 LLM (LM Studio) 集成环境
- [x] 实现 `LMStudioLLM` 原生适配器，解决 502 Bad Gateway 问题
- [x] 实现 指令桥接解析逻辑 (Prompt-based Tool Selection)，解决 Schema 兼容性问题
- [x] 优化工具适配器，放宽可选参数校验 (Any/Empty String Default)
- [x] 实证全链路本地化运行：Orchestrator 正确作出决策并调度 MCP 工具
- **状态：** complete

## 关键待办问题 (Critical Todos)
<!-- 
  内容：必须解决的关键代码点、潜在错误或不确定性。
  原因：防止在多步操作中遗漏细节。
-->
- [ ] 确保 v1 的 `AgentNodes` 调用与当前 `MCPToolClient` 兼容
- [ ] 设计事实的冲突处理逻辑（如果不同 Agent 发现矛盾的事实）

## 错误详志 (Error Log)
<!-- 
  内容：记录你遇到的阻碍性错误及其解决方法。类似于“经验教训”。
  原因：如果你再次遇到相同的错误，可以快速修复它。
-->
| 错误 | 原因 | 解决方案 |
|-------|--------|------------|
|       |        |            |

## 进度记录 (Progress Tracker)
<!-- 
  内容：已完成工作的简要时间线。
  原因：向用户展示进展并保持动力。
-->
- [2026-02-11] 任务启动：CLI 恢复与事实仓库增强。
- [2026-02-11] 本地化突破：成功实现 LM Studio 高性能集成，解决 SDK 兼容性及工具调用冲突。
