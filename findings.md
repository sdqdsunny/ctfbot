# 调研发现与决策 (Findings & Decisions)

## 需求项

- **CLI 完整性**：`run_v1` 和 `run_v2` 必须具有实际的执行输出，而不仅仅是 `pass`。
- **事实仓库 (Fact Store)**：
  - 结构化存储：支持键值对或分类存储发现。
  - 跨 Agent 共享：子 Agent A 的发现应能被总指挥传递给子 Agent B。
  - 决策辅助：Orchestrator 应根据 Fact Store 调整策略。

## 研究发现

- **v2 状态**：`run_v2` 已经具备了基本的环境设置（LLM, Tools, Graph），只差 `astream` 后的循环输出逻辑。
- **v1 状态**：`run_v1` 完全缺失，需要引用 `graph.workflow.create_agent_graph`。
- **AgentState**：现有的 `AgentState` 没有 `fact_store` 字段，需要扩展。

## 技术决策

| 决策 | 理由 |
|----------|-----------|
| **Fact Store 使用 Dict[str, Any]**| 灵活性高，适合处理不确定的 CTF 发现 |
| **Orchestrator 负责合并事实** | 保持子 Agent 的无状态/轻量化，逻辑集中管理 |

## 遇到的问题

| 问题 | 解决方案 |
|-------|------------|
| 'list' object error | sub-agent `astream` 在某些情况下（如多节点同步更新或特定 LLM 行为）可能返回非 dict 类型事件（如 list），导致 `.items()` 崩溃。 | 在循环前增加 `isinstance(event, dict)` 校验，并对常见的 list 包裹进行解包处理。 |

## 资源链接

- CLI 入口: `src/asas_agent/__main__.py`
- 状态定义: `src/asas_agent/graph/state.py`
- 工作流工厂: `src/asas_agent/graph/workflow.py`

## 视觉与浏览器发现 (Visual/Browser)

- (暂无)

---
*每进行 2 次视图/浏览器/搜索操作后更新此文件*
*这可以防止视觉信息丢失*
