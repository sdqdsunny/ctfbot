# v6.0 Distributed Swarm & GPU Acceleration Implementation Plan

**Goal:** Transform CTF-ASAS into a high-performance distributed cluster capable of massive parallel fuzzing and hardware-accelerated cryptanalysis.

**Context:** Final stage of the v5.0+ vision. Orchestrator now manages an elastic pool of "Swarm Workers".

---

## Phase A: Distributed Infrastructure (Ray)

### Task 1: Ray-based Worker Architecture

- [ ] **Step 1.1: Ray Integration Scaffolding**
  - Add `ray` to dependencies.
  - Implement `src/asas_agent/distributed/swarm_worker.py`: A wrapper for executing tools on remote nodes.
- [ ] **Step 1.2: Resource Metadata Discovery**
  - Logic to detect CPU cores/GPU types on each worker node.
  - Report status back to the Orchestrator via Ray's Global Control Store.

---

## Phase B: Multi-Node Parallel Fuzzing

### Task 2: Elastic Fuzzing Pool

- [ ] **Step 2.1: Distributed Docker Dispatcher**
  - Extend `DockerManager` to support remote Docker hosts (via `DOCKER_HOST`).
  - Tool: `pwn_fuzz_swarm_deploy(nodes_count)`: Simultaneously start fuzzer instances on multiple workers.
- [ ] **Step 2.2: Global Seed Synchronization**
  - Use Ray's `Plasma` object store to sync interesting seeds across all fuzzer nodes instantaneously.

---

## Phase C: GPU Acceleration (The "Hammer")

### Task 3: Hashcat Cracking Node

- [ ] **Step 3.1: GPU-Accelerated Cracking Tool (`gpu_hashcat_crack`)**
  - Tool logic: Detect hash type (SHA256, Zip, etc.) ⇨ Generate wordlist/bruteforce mask ⇨ Run Hashcat on GPU. Target workers with `GPU` tags.
- [ ] **Step 3.2: Automated Cryptanalysis Agent SOP**
  - Update `CryptoAgent`: If a known hash is found in leaks or files, automatically trigger the GPU cluster.

---

## Phase D: Local Intelligence & Optimization

### Task 4: Accelerated Local Inference

- [ ] **Step 4.1: TensorRT/Llama-cpp Integration**
  - Deploy efficient local LLMs (e.g., DeepSeek-7B) on each swarm worker.
  - Implement logic for workers to pre-audit results locally before sending them to the main Orchestrator.

---

## Phase E: Verification & Benchmarking

### Task 5: The "Horde Pressure" Test

- [ ] **Step 5.1: Create `tests/agent/test_v6_swarm_e2e.py`**
  - Scenario: A 10-node parallel fuzzing session + a 256-bit hash crack.
  - Verification: Measure time-to-exploit vs. single-node setup.

---

## Technical Stack

- **Ray**: Distributed compute orchestration.
- **Hashcat**: GPU cracking engine.
- **Docker-py (Remote mode)**: Managing containers across the network.
- **vLLM / Llama.cpp**: Accelerated local inference.
