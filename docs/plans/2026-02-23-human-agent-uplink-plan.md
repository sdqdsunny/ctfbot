# 人机协同交互增强实施计划 (Human-Agent Uplink Enhancement Plan)

## 背景与目标 (Goal Description)

继续提升 Command Center 的核心交互能力。重点完善 `OrchestratorChat`，引入干预机制，包括拦截危险操作（审批卡片）以及通过聊天框下发指令调整 Agent 运行逻辑。

1. **危险操作拦截 (Action Approval)**：Agent 尝试执行敏感操作（如覆盖文件、强力扫描）时，UI 应该能够渲染出一个特定样式的“Approval Card”（审批卡片），上面有 Approve / Reject / Modify 的按钮。
2. **主动干预指令 (Active Intervention)**：用户可以在聊天框发送指令，UI 需支持将这些指令回传到后端，用于打断或调整当前的 Agent 推理流程（前端侧重于搭建好 WebSocket Send 或 HTTP POST 的链路机制和 UI 反馈）。
3. **聊天记录与状态反馈**：强化 `OrchestratorChat` 内的系统提示，比如正在等待用户反馈时的状态展示。

## 需要用户审核的内容 (User Review Required)
>
> [!NOTE]
> 设计方向：
>
> 1. 数据结构：我们需要扩展现有的 `AgentEvent` 或是重新定义一下用于 Approval 的消息。为简单起见，我们将设定特定的 `lastEvent.type === 'action_approval'`。
> 2. 后端通信：前端目前只接收 WebSocket 事件。对于干预指令和审批结果，我们将通过 HTTP POST 到 `ui_server.py` 的 `/api/chat` 和 `/api/approve`，后续留给 Agent 引擎对接。
> 请确认以下组件改造是否符合您的预期要求。如果没有问题，我们将进入执行阶段。

## 具体更改提案 (Proposed Changes)

### 1. 聊天面板组件强化 (OrchestratorChat Enhancements)

#### [MODIFY] `ui/src/components/OrchestratorChat.tsx`

- **支持发送消息到后端**：改造 `handleSendMessage`，不仅在 UI 上追加 `userMsg`，还要将消息通过 HTTP POST 发送到 `http://localhost:8010/api/chat`（暂不要求后端立刻响应此接口的完美 Agent 逻辑，只需把链路搭好，能在 UI 呈现即可）。
- **支持审批卡片渲染**：扩充消息类型判断，如果在 websocket 收到了 `type === 'action_approval'`，则在聊天流里渲染出一个高亮的带有动作详情和 Approve/Reject 按钮的区块。

### 2. 交互动作组件 (Action Approval Card)

#### [NEW] `ui/src/components/chat/ApprovalCard.tsx`

- 为了保持代码整洁，将审批卡片单独拆分成一个组件。
- 采用赛博朋克风格警告配色（Amber/Rose），包含代码块显示待执行的指令。

### 3. 后端模拟接口 (Backend Stubs for UI Testing)

#### [MODIFY] `src/asas_agent/ui_server.py`

- 添加简单的 `@app.post("/api/chat")` 和 `@app.post("/api/approve")` 端点，只是简单返回 success，或将消息 broadcast 回 UI 以供测试。这保证了前端的网络请求不会 404，为真正的 Agent 暂停/继续引擎打好地基。

## 验证计划 (Verification Plan)

### 自动与静态检查

- 运行 `cd ui && pnpm lint` 确保组件的 TypeScript 强类型定义正确。

### 手动 UI 检查 (本地开发服务器)

- 在 UIEmitter 测试脚本中手动发放一个 `action_approval` 事件，验证前端聊天框是否能正确渲染出 `ApprovalCard`。
- 测试在输入框输入指令并发送，观察后端终端是否正确接收到了 POST `/api/chat` 的请求。
