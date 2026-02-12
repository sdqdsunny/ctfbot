# Task Plan: v5.1 Angr Symbolic Execution Integration

## Goal

Integrate Angr into the ReverseAgent via MCP to enable automated path solving and logic decryption (Stage 1 of v5.0 Swarm Architecture).

## Status Summary

- **Overall Status**: `v5.5 Horde Interoperability Complete` ✅
- **Start Date**: 2026-02-12
- **Current Milestone**: `v5.5 Hybrid Cluster Fully Operational` 🏁

---

## 🛠 原子任务清单 (Atomic Task List)

### Phase A: Core Angr Tool Implementation

- [x] **Task 1: 实现 Angr 路径解算工具 (`reverse_angr_solve`)**
  - [x] Step 1.1: 编写失败的单元测试 `tests/tools/test_reverse_angr.py`
  - [x] Step 1.2: 实现工具逻辑 `src/asas_mcp/tools/reverse_angr.py`
  - [x] Step 1.3: 通过测试并验证工具可用性
- [x] **Task 2: 实现约束解算助手 (`reverse_angr_eval`)**
  - [x] Step 2.1: 实现基于 JSON 定义的符号变量并行解算工具

### Phase B: Agent Integration & SOP Upgrade

- [x] **Task 3: 升级 ReverseAgent 装备**
  - [x] Step 3.1: 在 `reverse.py` 中注册 Angr 工具
  - [x] Step 3.2: 升级 System Prompt，注入“引导式挖掘(Guided Hunting)”逻辑
- [ ] **Task 4: 知识库同步更新**
  - [ ] Step 4.1: 在 RAG 系统中注入 Angr 高级用法 Demo 事实

### Phase C: E2E Verification

- [x] **Task 5: CrackMe 综合实战演练**
  - [x] Step 5.1: 编写 E2E 测试脚本，模拟“IDA 发现目标 -> Angr 自动解算”全流程

### Phase D: Fuzzing Engine Integration (v5.2)

- [x] **Task 6: 容器化 Fuzzing 基础设施**
  - [x] Step 6.1: 编写 `docker/Dockerfile.fuzzer` (AFL++ & QEMU)
  - [x] Step 6.2: 实现 `docker_manager.py` 容器调度器
- [x] **Task 7: 实现 Fuzzing 控制与 Triage 工具**
  - [x] Step 7.1: 实现 `pwn_fuzz_start` (异步启动 Fuzzer)
  - [x] Step 7.2: 实现 `pwn_fuzz_triage` (自动崩溃分析报告)
- [x] **Task 8: Agent 协同与 SOP 升级**
  - [x] Step 8.1: 更新 ReverseAgent 的 Pwn 挖掘逻辑

### Phase E: Horde Interoperability (v5.5)

- [x] **Task 9: 种子库交换机制**
  - [x] Step 9.1: 扩展 `DockerManager` 支持种子提取与回灌
  - [x] Step 9.2: 实现种子处理器 (Fuzz-Seed to Angr-Input)
- [x] **Task 10: 瓶颈感知与反馈环**
  - [x] Step 10.1: 升级 `pwn_fuzz_check` 支持结构化遥测数据
  - [x] Step 10.2: 实现“引导式混合求解工具” (Seed-guided Symbology)
- [x] **Task 11: 闭环 E2E 实战验证**
  - [x] Step 11.1: 编写“突破 4 字节魔数校验”的协同攻击 E2E 测试

---

## 📈 进度跟踪 (Progress Logs)

- **2026-02-12 (Morning)**: 完成 v5.1 Angr 核心集成与 E2E 验证。
- **2026-02-12 (Afternoon)**: 完成 v5.2 调研，确立容器化 Fuzzing 方案，开启原子任务分解。
