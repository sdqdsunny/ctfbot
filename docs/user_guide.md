# CTF-ASAS 用户使用指南 (CTF-ASAS User Guide)

欢迎使用 **CTF-ASAS (Automated Solving Agent System)**。本手册旨在帮助 CTF 选手快速掌握本系统的功能特点、使用方法及实战技巧。系统核心理念是利用 LLM 的决策能力驱动专业安全工具链。

---

## 🛠️ 项目核心功能 (Core Feature Log)

### 1. 军械库：Kali Linux 虚拟机集成 (v4.0 核心)

- **原生连接**：Agent 通过 `vmrun` 驱动直接桥接至本地 VMware 中的 Kali 虚拟机。
- **“上帝模式”指令注入**：绕过传统的 SSH 网络协议，直接通过 VMware 虚拟总线注入指令，具备极高的稳定性与安全性。
- **专业工具链**：
  - **Web 渗透**：`kali_sqlmap`, `kali_dirsearch`, `kali_nmap`。
  - **图片/隐写**：`kali_steghide`, `kali_zsteg`。
  - **Misc & 文件提取**：`kali_binwalk`, `kali_foremost`。
  - **流量分析**：`kali_tshark` 分析 pcap 数据包。
  - **通用执行**：`kali_exec` 支持执行任意 shell 命令。

### 2. 安全沙箱隔离 (Sandbox Isolation - v3.5)

- **多语言驱动**：支持在一秒内拉起隔离的 Docker 容器运行 Python 或 Bash 脚本。
- **强制约束**：
  - **禁用网络**：`--network none` 防止 Flag 被脚本窃取回传。
  - **资源限制**：限制内存 (128mb) 和 CPU (0.5)，防止拒绝服务攻击 (DoS) 或 Fork 炸弹。
  - **只读挂载**：容器根文件系统只读，仅保留极小的 `/tmp` 可写空间。
- **适用场景**：自动解密脚本、复杂的数学计算、或者运行来源不明的脚本题目。

### 3. 多路径决策系统 (v3.0 任务树)

- **回溯机制 (Backtracking)**：Agent 不再是单一路径运行，当某一探测路径（如目录扫描）发现多个线索时，会构建任务树并依次尝试。
- **上下文感知 (Context Awareness)**：Agent 具备记忆能力，会根据 `task_history` 避开已失败或重复的路径，实现真正的智能化渗透。

### 3. 平台自动化对接 (v1.5 引入)

- **自动取题**：支持通过题目 URL 自动抓取题目描述、分值及分类。
- **语义理解**：Agent 自动分析抓取到的描述，智能识别匹配的解题工具链。
- **自动提交**：系统识别出 Flag 后，可自动向 CTF 平台（如 CTFd）提交并获取得分状态。
- **递归状态机**：基于 LangGraph 实现了“感知->规划->执行->反馈”的循环，支持多步骤解题。

### 3. 深度逆向分析 (v2.0 已上线)

- **Ghidra Docker 化集成**：集成 `blacktop/ghidra` 镜像，支持无需本地安装的自动化反编译。
- **自动反编译**：Agent 可以调用 `reverse_ghidra_decompile` 提取二进制文件的全量 C 伪代码。
- **语义分析（v2.5 进行中）**：Agent 具备理解 C 伪代码逻辑的能力，可识别加密常量及算法流程，并尝试生成 Python Solver。
- **逻辑蒸馏**：[开发中] 提取代码中的常量、S-Box 和关键决策点，减少 LLM 推理干扰。

### 3. Web 自动化渗透 (v2.0 增强)

- **目录扫描 (web_dir_scan)**：内置轻量级字典，支持自动化路径探测。
- **注入检测 (web_sql_check)**：支持基于报错的 SQL 注入初步自动化检测。
- **内链爬取 (web_extract_links)**：自动提取页面中的所有 URL 和 Form 结构，辅助 Agent 扩展攻击面。

### 4. 跨题型工具链 (MCP Enabled)

- **Crypto 模块**：万能 Base64/Hex/URL 解码，新增 **摩斯密码 (Morse)**、**凯撒密码 (Caesar)** 爆破、**ROT13**，支持自动识别。
- **Recon 模块**：集成网络指纹探测与多端口扫描。
- **Reverse 模块**：二进制文件静态特征提取与敏感字符串扫描。
- **Misc 模块**：文件头识别与元数据解析。

### 4. RAG 本地记忆层

- **知识持久化**：集成 ChromaDB，Agent 会自动存储解题过程中的关键发现（事实仓库）。
- **经验检索**：支持对历史 Writeups 和解法搜索。

---

### 🛡️ 路线图 (Roadmap)

- [x] v1.5：基础平台对接与自动化提交
- [x] v2.0：Ghidra Docker 化集成与自动反编译
- [x] v2.5：基于 LLM 的语义分析与 Solver 自动生成
- [x] v3.0：支持多路径探测的任务树与回溯系统 (Backtracking)
- [x] v3.5：强隔离 Docker 安全沙箱
- [x] v4.0：Kali Linux 虚拟机实战军械库集成
- [ ] v4.5：**智能 IDA Pro 助手集成** (预计通过 `ida-pro-mcp` 实现深度交互)
- [ ] v5.0：分布式协同渗透与大规模自动化解题

---

## 📖 使用方法 (Usage Instructions)

### 1. 基础任务执行

```bash
python -m src.asas_agent "请解码这段 Base64: SGVsbG8gQVNBUw=="
```

### 2. 平台实战模式 (API 联动)

```bash
python -m src.asas_agent --url "http://[CTF_URL]/api/v1/challenges/[ID]" --token "[YOUR_API_TOKEN]"
```

### 3. 真实 LLM 模式

```bash
python -m src.asas_agent --llm claude --api-key "your_sk_key" "你的解题指令"
```

---

## 📦 安装与部署

- **一键安装**: `bash scripts/install.sh`
- **Windows**: 使用 `dist/ctfbot-windows.exe`
- **GitHub Actions**: 推送 Tag 自动构建多平台发行版。

---

## 📝 开发者备注

### 最近完成任务 (2026-02-07)

- **Kali 工具链扩展**：新增 `kali_binwalk` 和 `kali_foremost` 工具，增强了 Misc 题型的自动化提取能力。
- **Agent 稳定性修复**：修复了 MockLLM 的意图识别优先级冲突，解决了在复杂任务中的递归循环 (Recursion Error) 问题。
- **全流程自动化验证**：通过了涉及“逆向反编译 -> 语义分析 -> 脚本生成 -> 自动提交”的全链路逻辑测试。
- **文档同步机制**：确立了开发进展与用户指南同步更新的规范。

*本手册将随着项目功能的迭代动态更新。*
