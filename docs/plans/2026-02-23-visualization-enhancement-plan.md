# 核心节点流可视化深化实施计划 (Visualization UI/UX Enhancement Plan)

## 背景与目标 (Goal Description)

继续提升 Command Center 的视觉体验。针对当前比较基础的 React Flow `ProcessGraph` 进行深度的赛博朋克主题定制：

1. **节点视觉强化**：添加发光效应、根据 Agent 执行状态（如 Pending, Running, Success, Failed）切换不同颜色与动画。
2. **连线动效**：实现数据流连线的微动效（如霓虹光束穿梭效果）。
3. **交互与面板集成**：将 React Flow 节点的点击事件与 `PayloadInspector` 面板打通，实现节点检查器逻辑流转。

## 需要用户审核的内容 (User Review Required)
>
> [!NOTE]
> 设计方向：整体仍旧沿用现有的暗黑赛博朋克风 (深底色 + 霓虹紫/青配色)。
> 请确认以下组件拆分与实现细节是否符合您的预期要求。如果没有问题，我们将进入执行阶段。

## 具体更改提案 (Proposed Changes)

### 1. 自定义 React Flow 节点组件设计 (Custom Agent Node)

#### [NEW] `ui/src/components/graph/AgentNode.tsx`

- 创建自定义节点以替代 React Flow 默认节点。
- 支持 `data.status` 属性（`pending`, `running`, `success`, `error`）。
- 使用 Framer Motion 与 CSS 结合实现：外发光 (Box-shadow glow)、脉冲呼吸灯效果 (Pulse animation)。

### 2. PayloadInspector 面板对齐交互集成 (Inspector Integration)

#### [MODIFY] `ui/src/components/CommandCenter.tsx`

- 将选中的节点状态拉升到父组件（或在 `ProcessGraph` 内自己管理面板状态）。目前 `PayloadInspector` 在 `CommandCenter` 被引入。管理其展示状态（`nodeId`）。

#### [MODIFY] `ui/src/components/PayloadInspector.tsx`

- 完善展示逻辑，后续可以基于传入的 `data` 属性动态显示推断结果和 Payload 日志，而不是纯静态硬编码。

### 3. ProcessGraph 核心画布强化 (ProcessGraph Enhancements)

#### [MODIFY] `ui/src/components/ProcessGraph.tsx`

- 注册并使用自定义的 `AgentNode` (即 `nodeTypes={{ agent: AgentNode }}`)。
- 配置节点的 `onNodeClick` 事件，触发打开 `PayloadInspector` 面板。
- 配置边 (Edges) 为带有动画的虚线，或者开发 [NEW] `AnimatedEdge` 实现霓虹光束滑动效果 (SVG dash array 动画)。
- 建立一套初始带有层测的节点群示例用于展示效果。

## 验证计划 (Verification Plan)

### 自动与静态检查

- 运行 `pnpm lint` 确保 React 组件的类型严谨性 (避免 any 报错)。

### 手动 UI 检查 (本地开发服务器)

- 直接在浏览器中观察节点的外发光、状态切换动画以及边上的流动粒子效果。
- 鼠标点击图表节点，观察侧边 `PayloadInspector` 是否平滑弹出并展示对应的 ID 和模拟数据。
