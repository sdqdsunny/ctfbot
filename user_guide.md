# CTF-ASAS 用户指南 (User Guide)

本文档记录了 CTF-ASAS 系统架构及其演进路线。

---

## 🛠 当前稳定版本 (v4.5): IDA Pro 深度集成

v4.5 实现了基于 Orchestrator 编排的 IDA Pro 自动化分析：

- **Headless Analysis**: 无头模式自动扫描。
- **Agent Coordination**: Orchestrator 自主调度子代理使用 IDA Pro 工具链。
- **Fact Store**: 跨代理的结构化事实共享。

---

## 🚀 规划中版本 (v5.0): 自进化漏洞挖掘集群 (Horde Architecture)

### 1. 核心愿景 (Vision)

v5.0 旨在将系统从“自动化工具使用者”进化为“自主全能安全研究员”，具备并行竞争、资源动态调优和跨引擎反馈学习的能力。

### 2. "Horde" (蜂群) 集群架构

系统采用并行竞争模式，不再进行单一任务分发，而是同时启动多个专业引擎：

| 组件名称 | 技术栈 | 职责描述 |
| :--- | :--- | :--- |
| **SymmNode (符号执行)** | Angr / Triton | 处理硬核逻辑校验、多分支寻路。 |
| **FuzzNode (模糊测试)** | AFL++ / LibFuzzer | 在容器化集群中探索边界，寻找 Crash。 |
| **IntuitionNode (AI 推理)** | LLM / IDA Pro | 静态扫描 C 代码，识别常见的内存/逻辑漏洞。 |

### 3. 自进化反馈机制: 动态算力调度 (DRC)

这是 v5.0 的核心进化特征，Orchestrator 通过 **遥测总线 (Telemetry Bus)** 监控各个引擎：

- **优先级竞争**: 所有引擎并行运行。
- **动态权重分配**: 如果 Fuzzer 的 Coverage 增长显著，系统自动迁移 CPU/内存资源支持它。
- **反馈学习**: 符号执行找到的合法路径会转化为种子（Seeds）实时推给 Fuzzer，实现引擎间的深度协同。

### 4. 数据流设计 (Data Flow)

1. **Mission Start**: Orchestrator 全副本下发任务。
2. **Telemetry Loop**: 持续监控各引擎 of Coverage、Path 数和 Crash 信号。
3. **Resource Shake**: DRC 根据遥测数据实时调整资源状态（挂起/提速）。
4. **Solve & Merge**: 任何引擎输出 Flag/Payload 即宣告任务完成，其余引擎强制释放。

### 5. 协同进化逻辑: "引导式挖掘" (Guided Hunting)

并行引擎不再孤岛运行，而是通过以下通道共享关键信息：

- **AI ⇨ Symb (导航模式)**: IntuitionNode 静态分析发现溢出嫌疑点，向 SymmNode 下达目标地址，触发精准路径解算。
- **Symb ⇨ Fuzz (动力交换)**: SymmNode 解出的复杂分支输入值实时作为种子（Seed）同步给 FuzzNode，帮助 Fuzzer 跨越逻辑屏障。
- **Crash ⇨ AI (成果转化)**: FuzzNode 捕获崩溃后，由 AI 结合 Register/Memory 现场自动分析漏洞类型并尝试生成 Exploit。

### 6. 实施路线图 (v5.0 Implementation Roadmap)

#### 第一阶段 (v5.1): 符号执行先锋

- **核心工具**: 基于 **Angr** 动态二进制框架。
- **目标**: 实现 `reverse_agent_solve_path` 工具，让 Agent 能在 IDA 辅助下自主定义约束条件。

#### 第二阶段 (v5.2): 分布式模糊测试 (FuzzNode)

- **核心工具**: **AFL++ (QEMU 模式)** 部署于 Docker 容器集群。
- **目标**: 建立容器化 Fuzzing 池，实现自动 Triage（崩溃现场分析）。
- **收割 SOP**: 发现 Crash 后自动提取寄存器和堆栈状态（GDB-exploitable）并反馈给 Orchestrator。

#### 第三阶段 (v5.5): Swarm 合体 (Deep Interoperability)

- **目标**: 实现 **Fuzz ⇨ Angr ⇨ AI** 的闭环协同逻辑。
- **核心逻辑**: FuzzNode 发现的路径输入自动同步给 Angr，作为初始状态帮助其绕过 Fuzzer 无法克服的复杂分支校验。

---
