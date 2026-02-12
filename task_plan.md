# 任务计划：CTF-ASAS v5.x - v6.0 开发与集成

## 目标

实现 CTF-ASAS 从单机工具集成到分布式蜂群（Swarm）架构的全面进化，包括符号执行（Angr）、模糊测试（AFL++）、引擎协同（Horde Bridge）以及分布式 GPU 加速（Ray & Hashcat）。

## 当前阶段

阶段 4：交付与回顾 (v6.0 已完成验证)

## 阶段规划

### 阶段 1：v5.1 Angr 核心集成

- [x] 实现 `reverse_angr_solve` 和 `reverse_angr_eval` 工具
- [x] 更新 `ReverseAgent` SOP 以支持 Guided Hunting 策略
- [x] 编写并通过 E2E 测试 `test_angr_e2e_v5.py`
- **状态：** complete

### 阶段 2：v5.2 Fuzzing 基础设施 (FuzzNode)

- [x] 编写 `docker/Dockerfile.fuzzer` (AFL++ & QEMU)
- [x] 实现 `DockerManager` 容器调度器
- [x] 实现 `pwn_fuzz_start` 和 `pwn_fuzz_triage` 工具
- [x] 编写并通过 E2E 测试 `test_fuzz_e2e_v5.py`
- **状态：** complete

### 阶段 3：v5.5 引擎间深度协同 (Horde Interoperability)

- [x] 扩展 `DockerManager` 支持种子提取与回灌
- [x] 实现 `horde_bridge` 工具集
- [x] 升级 `ReverseAgent` 支持 Stagnation-aware 调度
- [x] 编写并通过 E2E 测试 `test_horde_e2e_v5.py`
- **状态：** complete

### 阶段 4：v6.0 分布式 Swarm 与 GPU 加速

- [x] **Swarm Fabric**: 实现基于 Ray 的 `ClusterManager`, `SwarmRouter`, `SwarmWorker` (支持 Capability Discovery & Reputation)
- [x] **Swarm Fuzzing**: 实现 `SeedJanitor` (全局种子同步) 和 `ConcolicBreaker` (Angr 破局闭环)
- [x] **Swarm GPU**: 实现 `GPUJobManager` (支持优先级抢占 & 故障漂移) 和 `gpu_hashcat` 适配
- [x] 编写并通过 E2E 测试 `test_v6_swarm_full_fuzzing_synergy.py` 和 `test_v6_swarm_gpu_fault_tolerance.py`
- **状态：** complete

## 决策记录

| 决策 | 理由 |
|----------|-----------|
| 使用 Ray 作为分布式底座 | 相比 K8s 更轻量，支持动态资源发现（GPU/CPU），适合 CTF 场景 |
| 种子库同步 (Corpus-based) | 实现简单且稳健，参考了 Driller 的成功经验 |
| Stagnation-Driven 触发 | 模拟黑客“暴力无效后切入手动/符号分析”的思维逻辑，节省算力 |

## 遇到的错误

| 错误 | 尝试次数 | 解决方案 |
|-------|---------|------------|
| E2E 测试断言失败 (Locale) | 1 | 将测试中的英文匹配改为中文“栈溢出” |
| DockerManager 状态丢失 | 2 | 增加了 `_container_mounts` 进行元数据追踪 |
| Pip 安装依赖超时/证书错误 | 2 | 记录在案，本地环境需注意代理配置 |
