# 后端人机链路实施计划 (Backend Human-Agent Uplink Plan)

## 背景与目标 (Goal Description)

在上一个任务中，我们已经打通了前端 UI 发送干预指令（Chat）和动作审批（Approve）到 `ui_server.py` 的 HTTP 接口。
由于我们当前的架构是分离进程的（CLI 主进程独立运行 Agent，UI Server 作为独立进程广播 WebSocket），我们需要一种进程间通信 (IPC) 机制，让 CLI 的 Agent 能“感知”到 UI Server 收到的用户输入与审批决定。因为这是一个简单的本地化应用，**轮询 (Polling)** 是最稳妥的 MVP 选择。

## 需要用户审核的内容 (User Review Required)
>
> [!NOTE]
> 设计方向：
>
> 1. **审批同步阻塞**：当 Agent 在 LangGraph 的 ToolNode 中准备执行危险指令（如 `kali_exec`, `kali_sqlmap`）时，它会触发 `action_approval` 事件给 UI Server，然后原地陷入 `while True: await asyncio.sleep(1)`，去 HTTP GET 轮询 UI Server 上的审批状态，直到获得 Approve / Reject。
> 2. **聊天消息截获**：在 Orchestrator Agent 的每一个 Graph Node 执行前，通过 HTTP GET 轮询拉取 UI 发来的待处理 User Chat Message，并将其作为新的 `HumanMessage` 注入到 State 的 `messages` 队列末尾，强行改变 Agent 的推理上下文。

请确认以下代码改造方案是否符合您的预期要求。如果没有问题，我们将进入执行阶段。

## 具体更改提案 (Proposed Changes)

### 1. 扩充状态存储与轮询接口

#### [MODIFY] `src/asas_agent/ui_server.py`

- 在内存中定义 `_approvals: dict` 和 `_pending_chats: list` 来存储状态。
- 为 `/api/chat` 和 `/api/approve` 添加存储逻辑。
- [NEW] 增加 `GET /api/approval_status/{action_id}`，让 CLI 能够轮询。
- [NEW] 增加 `GET /api/pending_chats`，返回并清空列表（Pop 语义），供 CLI 获取最新的用户干预指令。

### 2. 核心 ToolNode 添加审批拦截器

#### [MODIFY] `src/asas_agent/graph/workflow.py` (或者在工具调用的执行器里)

- 定义高危工具列表 `DANGEROUS_TOOLS = ["kali_exec", "kali_sqlmap", "run_script"]`。
- 修改或者包装原生的 `ToolNode`：如果是高危工具，生成一个 Unique Action ID。
- 用 `ui_emitter.emit("action_approval", ...)` 广播给前端。
- 使用 `httpx` 或 `requests` 每隔 1.5 秒轮询 UI Server 的 `approval_status`。
- 【Approved】: 真实执行该工具。
- 【Rejected】: 直接短路，返回 `ToolMessage(content=f"User Interaction: tool execution REJECTED with feedback: {feedback}")`。

### 3. Orchestrator Node 拦截与聊天消息注入

#### [MODIFY] `src/asas_agent/graph/workflow.py`

- 在 `orchestrator_node` 函数的起步阶段，发起短连接轮询 `GET /api/pending_chats`。
- 如果拉取到了数组数据，则将其包装为 `HumanMessage(content=f"【用户实时指令】: {msg}")`，并 append 到 `messages` 列表的尾部（或者覆盖到 `system_prompt` 中），以立刻改变 LLM 接下来的意图判断。

## 验证计划 (Verification Plan)

### 自动与静态检查

- 本地编写 `pytest` 测试脚本模拟完整的轮询生命周期。

### 手动集成测试 (End-to-end)

- 启动终端 1: `poetry run uvicorn src.asas_agent.ui_server:app --port 8010`
- 启动终端 2: `pnpm dev`
- 启动终端 3: `poetry run python -m asas_agent run http://localhost -v3`
- 当 Agent 调用 `kali_exec` 时，UI 会弹出卡片。Agent 控制台会处于卡住打印 "Waiting for user approval..." 状态。界面点击 Approve 后，Agent 恢复执行。
- 聊天框输入文字发送后，Agent 在下一次图循环中，会理解该指令改变行为模式。
