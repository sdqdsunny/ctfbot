# CTF-ASAS 增强计划：Web 渗透与多维能力升级计划

## 阶段 1：Kali Linux 虚拟机深度集成 (Kali VM Integration)

**目标**：将本地 Kali 虚拟机转化为 Agent 的“远程军械库”，直接调用专业渗透工具。

- **构建 `KaliExecutor`**：通过 `vmrun` 或 SSH 建立与 Kali 虚拟机的稳定通道。
- **工具映射 (Kali Bridge)**：
  - `kali_sqlmap`: 调用虚拟机内的 sqlmap 进行漏洞利用。
  - `kali_dirsearch`: 调用虚拟机内的 dirsearch 进行路径探测。
  - `kali_nmap`: 执行完整的网络扫描。
- **环境自愈**：如果工具未安装，支持自动在虚拟机内执行 `apt install`。

## 阶段 2：v3.0 递归任务树架构 (Task Tree & Backtracking)

**目标**：解决 Agent “一根筋”的问题，支持多路径探索与失败回溯。

- **State 升级**：引入 `task_tree` 结构记录尝试过的路径。
- **决策层升级**：如果当前路径失败（如 SQL 注入无果），Agent 能够跳转回“任务树”的父节点，尝试“路径扫描”分支。

## 阶段 3：图片隐写与 Misc 综合能力 (Steganography & Misc)

**目标**：利用 Kali 内置的专业工具解决 Misc 题目。

- **隐写分析**：调用 `steghide`, `stegsolve`, `zsteg` 等工具。
- **流量分析**：调用 `tshark` 分析 pcap 文件。

## 阶段 4：专业级 IDA Pro 智能助手集成 (IDA Pro MCP Integration)

**目标**：将业界顶尖的逆向工具 IDA Pro 接入 Agent 工具链，实现交互式智能逆向。

- **MCP 桥接**：集成 `mrexodia/ida-pro-mcp`，实现 Agent 与 IDA Pro 的双向通信。
- **高级逆向指令**：
  - `ida_decompile`: 获取比 Ghidra 更精准的函数反编译结果。
  - `ida_rename`: 让 Agent 自动根据语义逻辑重命名 IDA 中的变量与函数名。
  - `ida_patch`: 允许 Agent 直接在 IDA 中下发指令进行代码修补（Patching）。
  - `ida_xrefs`: 智能查询交叉引用，辅助 Agent 梳理程序调用拓扑。
- **Headless 自动化**：探索集成 `idalib`，实现在无 UI 环境下由 Agent 自动完成 IDA 分析并产出解题报告。

---
Thought in Chinese: 循序渐进地构建一个全能 Agent。首先从 Web 自动化开始，因为这是 CTF 中最高频的场景。
