# CTF-ASAS 平台自动化对接口 (v1.5) 设计方案

## 1. 目标

实现 Agent 与 CTF 平台（以 CTFd 为主）的自动化交互，完成从“获取题目”到“提交 Flag”的全流程闭环。

## 2. 核心功能

- **F1: 平台认证 (Authentication)**: 支持 API Token 或 Session 登录。
- **F2: 题目拉取 (Challenge Fetching)**: 自动获取题目描述、附件链接、题目分类。
- **F3: 环境识别 (Target Discovery)**: 自动提取动态环境的 IP/Port 或 URL。
- **F4: 自动提交 (Auto-Submission)**: 解码获取 Flag 后，自动调接口提交并记录结果。

## 3. 架构设计

### 3.1 模块结构

```text
ctfbot/
├── src/
│   ├── asas_mcp/
│   │   ├── tools/
│   │   │   └── platform.py      # [新增] 平台交互工具集
│   │   └── server.py            # [更新] 注册新工具
│   └── asas_agent/
│       ├── graph/
│       │   └── nodes.py        # [更新] 增加平台操作逻辑节点
│       └── __main__.py         # [更新] 支持 --url 参数直接启动
```

### 3.2 MCP 工具定义 (New Tools)

- `platform_get_challenge(url: str)`: 解析题目详情。
- `platform_submit_flag(challenge_id: str, flag: str)`: 提交答案。
- `platform_download_attachment(file_url: str)`: 下载题目附件到本地临时目录。

## 4. 实施策略 (Implementation Plan)

### 第一步：基础工具实现

- 选择一个常用的 CTF 平台框架（CTFd）进行适配。
- 实现 `platform` 工具类，封装 `requests` 调用。

### 第二步：Agent 链路整合

- 修改 `AgentState`，增加 `challenge_meta` 和 `flag_found` 字段。
- 增加 `FETCH_CHALLENGE` 节点，作为图的起始分支。
- 修改 `FORMAT_RESULT` 节点，如果发现 Flag 则进入 `SUBMIT` 分支。

### 第三步：验证

- 使用一个本地搭建的 CTFd 实例或公开的练习平台进行端到端测试。

---
Thought in Chinese: 先写好设计文档，再逐步分解任务执行。
