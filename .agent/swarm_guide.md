# ASAS Agent v6.0 Swarm 集群部署指南

本文档将指导您如何部署和配置 **ASAS Agent v6.0 Swarm** 分布式集群，以启用并行 Fuzzing 和分布式 GPU 爆破功能。

---

## 🚀 架构概览

v6.0 Swarm 采用 **Ray** 作为底层的分布式通讯与任务调度框架。

* **Orchestrator (主控节点)**：运行 Agent CLI、LLM 决策层、FuzzManager 和 GPUJobManager。负责发号施令。
* **Worker (计算节点)**：运行 `SwarmWorker`，执行具体的 Fuzzing、Angr 解算或 Hashcat 爆破任务。

---

## 🛠️ 环境准备

### 1. 基础依赖

所有节点（Orchestrator 和 Worker）都需要安装 Python 环境和基础依赖：

```bash
# 在所有节点执行
pip install ray[default] docker psutil
```

### 2. 软件能力准备 (Worker 节点)

根据 Worker 的角色，提前安装必要的工具，Agent 会自动识别：

* **Fuzzing 节点**：安装 Docker 并预拉取 AFL++ 镜像。

    ```bash
    docker pull aflplusplus/aflplusplus
    ```

* **Angr/IDA 节点**：
  * 确保 `angr` 已安装：`pip install angr`
  * (可选) 设置 `IDA_PATH` 环境变量指向 IDA Pro。
* **GPU 爆破节点**：
  * 安装 Nvidia 驱动和 CUDA 工具包。
  * 确保 `hashcat` 在 PATH 中可用（或安装 `hashcat` 包）。
  * **验证**：运行 `nvidia-smi` 确保显卡在线。

---

## 🌐 启动集群

### 步骤 1：启动 Head 节点 (Orchestrator 所在机器)

在主控机器上启动 Ray Head 节点：

```bash
# 启动 Head 节点，指定 dashboard 端口（可选）
ray start --head --port=6379 --dashboard-host=0.0.0.0
```

*记录下输出中的 `Local node IP` 和 `Redis password`（如果有），后续 Worker 连接需要用到。*

### 步骤 2：启动 Worker 节点

在其他计算节点上，连接到 Head 节点：

```bash
# 将 <HEAD_IP> 替换为主控机 IP
ray start --address='<HEAD_IP>:6379'
```

### 步骤 3：验证集群状态

在主控机上使用 Agent CLI 查看集群状态：

```bash
python3 src/asas_agent/__main__.py swarm status
```

如果输出显示了多个节点信息，通过 `Active Nodes` 数量确认集群已组建成功。

---

## 🏷️ 高级配置：节点标签与资源

默认情况下，Agent 会自动探测 CPU、GPU 和内存信息。
如果你需要强制指定节点的角色（例如：将某台机器标记为 **"Angr 专家"**），可以在启动 Worker 时添加自定义资源标签（Ray Resources）：

```bash
# 在 Worker 节点启动时，添加自定义 resources
ray start --address='<HEAD_IP>:6379' --resources='{"role:expert": 1, "special_license": 1}'
```

Agent 的路由逻辑 (`SwarmRouter`) 支持根据这些标签进行精准调度。

---

## 🔥 运行分布式任务

### 1. 启动 Agent

确保环境变量 `RAY_ADDRESS` 指向集群（如果是在 Head 节点本地运行 Agent，通常不需要，或者设为 `auto`）：

```bash
export RAY_ADDRESS=auto
python3 src/asas_agent/__main__.py run --v3 --config v3_config.yaml
```

### 2. 验证 Fuzzing 协同

当 Agent 决定启动 `pwn_fuzz` 任务时：

1. 它会自动寻找空闲的 Worker 节点。
2. Orchestrator 的控制台会显示 `[SeedJanitor]` 日志，表明正在同步各节点的种子。
3. 如果发现 Logic Stuck，它会自动调度任务给 **Angr 节点**（如果存在）。

### 3. 验证 GPU 调度

当 Agent 遇到哈希爆破任务时：

1. 它会自动将任务投递给带 `GPU` 的节点。
2. 如果在爆破过程中有更高优先级的 Hash 出现，您可以观察到低优任务进入 `PAUSED` 状态。

---

## ❌ 常见问题排查

**Q: Worker 节点无法连接 Head？**

* A: 检查防火墙（6379, 8265, 10001-10010 端口）。确保所有节点时间同步。

**Q: Agent 提示 "No suitable worker found"？**

* A: 检查 `swarm status`。确认 Worker 节点是否具备任务所需的 `tags`（如 `gpu` 或 `angr`）。

**Q: Fuzzing 种子不同步？**

* A: 检查 Worker 节点的 Docker 挂载权限，以及网络是否允许 Ray Object Store 大流量传输。

---
**Enjoy your Swarm!** 🐝
