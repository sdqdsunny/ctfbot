# 调研发现与决策 (Findings & Decisions)

## 需求项

- 实现高效率的漏洞自动挖掘闭环。
- 支持单机多容器并行及跨机分布式调度。
- 整合符号执行、模糊测试、AI 推理及硬件加速（GPU）。

## 研究发现

- **AFL++ QEMU 模式**: 在没有源码的情况下，QEMU 模式是二进制模糊测试的最佳平衡点。
- **Angr 状态同步**: 通过注入 Stdin prefix 可以有效引导 Angr 从 Fuzzer 的快照点继续探索。
- **Ray 分布式**: Ray Cluster 的 Actor 模型非常适合管理状态持久的 Fuzzer 实例。
- **GPU 压制**: Hashcat 对特定 Hash 类型的爆破速度比 CPU 快 2-3 个数量级。

## 技术决策

| 决策 | 理由 |
|----------|-----------|
| 容器化方案 | 保证 Fuzzing 环境的可重复性与安全性隔离 |
| GDB-Exploitable | 成熟的 Crash 画像工具，能快速判定漏洞可利用性 |
| Base64 传输 | 解决 Docker exec 在处理二进制文件时的编码截断问题 |

## 资源链接

- AFL++ Repo: <https://github.com/AFLplusplus/AFLplusplus>
- Angr Documentation: <https://docs.angr.io/>
- Ray Framework: <https://www.ray.io/>
- 相关文件: `src/asas_mcp/executors/docker_manager.py`, `src/asas_agent/distributed/swarm_worker.py`

## 视觉与浏览器发现 (Visual/Browser)

- (本会话无浏览器视图，依赖静态分析与 CLI 输出)
- CLI 输出证实了 `afl-whatsup` 能够提供实时统计，是瓶颈感知的核心数据源。
