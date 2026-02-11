---
name: planning-with-files
version: "2.1.2"
description: 实现 Manus 风格的基于文件的复杂任务规划。创建 task_plan.md, findings.md, 和 progress.md。在开始复杂的、涉及多步分析、研究项目或任何需要 >5 步工具调用的任务时使用。
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebFetch
  - WebSearch
hooks:
  SessionStart:
    - hooks:
        - type: command
          command: "echo '[planning-with-files] 准备就绪。复杂任务将自动激活，或手动输入 /planning-with-files 启动'"
  PreToolUse:
    - matcher: "Write|Edit|Bash"
      hooks:
        - type: command
          command: "cat task_plan.md 2>/dev/null | head -30 || true"
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "echo '[planning-with-files] 文件已更新。如果此步骤完成了一个阶段，请更新 task_plan.md 的状态。'"
  Stop:
    - hooks:
        - type: command
          command: "/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/scripts/check-complete.sh"
---

# 基于文件的规划 (Planning with Files)

像 Manus 一样工作：使用持久化的 Markdown 文件作为你的“磁盘上的工作记忆”。

## 重要：文件存放位置

使用此技能时：

- **模板** 存储在技能目录中：`/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/`
- **你的规划文件** (`task_plan.md`, `findings.md`, `progress.md`) 应当创建在**你的项目根目录**中 —— 即你当前工作的文件夹。

| 位置 | 存放内容 |
|----------|-----------------|
| 技能目录 (`/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/`) | 模板、脚本、参考文档 |
| 你的项目根目录 | `task_plan.md`, `findings.md`, `progress.md` |

这确保了你的规划文件与代码并存，而不是埋在技能安装文件夹中。

## 快速上手

在开始任何复杂任务之前：

1. **在项目中创建 `task_plan.md`** —— 参考模板 [templates/task_plan.md](/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/task_plan.md)
2. **在项目中创建 `findings.md`** —— 参考模板 [templates/findings.md](/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/findings.md)
3. **在项目中创建 `progress.md`** —— 参考模板 [templates/progress.md](/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/progress.md)
4. **在做决定前重读计划** —— 刷新注意力窗口中的目标
5. **每个阶段完成后更新** —— 标记完成状态，记录错误

> **注意：** 所有三个规划文件都应创建在你当前的工作目录（项目根目录）中，而不是技能的安装文件夹中。

## 核心模式

```
上下文窗口 = RAM (易失, 有限)
文件系统 = 磁盘 (持久, 无限)

→ 任何重要的信息都必须写入磁盘。
```

## 文件用途

| 文件 | 用途 | 何时更新 |
|------|---------|----------------|
| `task_plan.md` | 阶段、进度、决策 | 每个阶段结束后 |
| `findings.md` | 研究、发现 | 任何发现后立即记录 |
| `progress.md` | 会话日志、测试结果 | 贯穿整个会话 |

## 核心规则

### 1. 计划先行

没有 `task_plan.md` 绝不开始复杂任务。这是底线。

### 2. “双动”原则 (The 2-Action Rule)
>
> “每进行 2 次 view/browser/search 操作后，必须立即将关键发现保存到文本文件中。”

这可以防止视觉或多模态信息（浏览器返回内容等）丢失。

### 3. 决定前先阅读

在做出重大决策之前，阅读计划文件。这能让目标始终保持在你的注意力窗口内。

### 4. 行动后必更新

完成任何阶段后：

- 标记阶段状态：`in_progress` → `complete`
- 记录遇到的任何错误
- 注明创建/修改的文件

### 5. 记录所有错误

每一个错误都要记录在计划文件中。这能积累知识并防止重复犯错。

```markdown
## 遇到的错误
| 错误 | 尝试次数 | 解决方案 |
|-------|---------|------------|
| FileNotFoundError | 1 | 创建了默认配置文件 |
| API timeout | 2 | 增加了重试逻辑 |
```

### 6. 绝不重复失败

```
if action_failed:
    next_action != same_action
```

追踪你尝试过的方法。改变思路，不要死磕。

## “事不过三”错误协议 (3-Strike Error Protocol)

```
尝试 1: 诊断并修复
  → 仔细阅读错误信息
  → 确定根本原因
  → 应用针对性修复

尝试 2: 替代方案
  → 同样的错误？换个方法
  → 换个工具？换个库？
  → 绝不重复完全相同的失败操作

尝试 3: 重新思考
  → 质疑所有前提假设
  → 寻找其他解决方案
  → 考虑更新整体计划

连续 3 次失败后：升级上报给用户
  → 详细解释你尝试了什么
  → 分享具体的错误信息
  → 寻求用户指导
```

## 读与写决策矩阵

| 场景 | 行动 | 原因 |
|-----------|--------|--------|
| 刚刚写入了一个文件 | 不要读取 | 内容还在上下文窗口中 |
| 查看了图片/PDF | 立即写入发现 | 多模态信息在丢失前转为文本 |
| 浏览器返回了数据 | 写入文件 | 网页内容不会持久存在 |
| 开始新阶段 | 阅读计划/发现 | 防止上下文窗口变旧导致跑偏 |
| 发生错误 | 阅读相关文件 | 需要当前状态来修复 |
| 间断后恢复任务 | 阅读所有规划文件 | 找回丢失的状态 |

## 重启自检 5 问 (The 5-Question Reboot Test)

如果你能回答这些问题，说明你的上下文管理非常稳固：

| 问题 | 答案来源 |
|----------|---------------|
| 我在哪里？ | `task_plan.md` 中的当前阶段 |
| 我要去哪？ | 剩余的阶段 |
| 目标是什么？ | 计划中的目标陈述 |
| 我学到了什么？ | `findings.md` |
| 我做了什么？ | `progress.md` |

## 何时使用此模式

**适用于：**

- 多步骤任务 (3 步以上)
- 研究任务
- 构建/开发项目
- 跨越多个工具调用的任务
- 任何需要组织严密性的工作

**可跳过：**

- 简单问题
- 单文件编辑
- 快速查询

## 模板

复制这些模板开始：

- [/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/task_plan.md](templates/task_plan.md) — 阶段追踪
- [/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/findings.md](templates/findings.md) — 研究存储
- [/Users/guoshuguang/my-project/antigravity/ctfbot/.agent/skills/planning-with-files/templates/progress.md](templates/progress.md) — 会话日志

## 脚本

用于自动化的辅助脚本：

- `scripts/init-session.sh` — 初始化所有规划文件
- `scripts/check-complete.sh` — 验证所有阶段已完成

## 反面模式 (Anti-Patterns)

| 禁止 | 建议 |
|-------|------------|
| 使用 TodoWrite 进行持久化 | 创建 task_plan.md 文件 |
| 只说一次目标就忘掉 | 决策前重读计划 |
| 隐藏错误或默默重试 | 将错误记录到计划文件中 |
| 将所有内容塞进上下文 | 将大数据内容存入文件 |
| 立即开始执行任务 | 先创建计划文件 |
| 重复失败的行动 | 追踪尝试，改变方法 |
| 在技能目录创建文件 | 在你的项目目录创建文件 |
