#!/bin/bash
# 初始化新会话的规划文件 (Chinese Version)
# 用法: ./init-session.sh [项目名称]

set -e

PROJECT_NAME="${1:-project}"
DATE=$(date +%Y-%m-%d)

echo "正在初始化规划文件，项目：$PROJECT_NAME"

# 创建 task_plan.md
if [ ! -f "task_plan.md" ]; then
    cat > task_plan.md << 'EOF'
# 任务计划：[简要描述]

## 目标
[描述最终状态的一句话]

## 当前阶段
阶段 1

## 阶段规划

### 阶段 1：需求分析与调研
- [ ] 理解用户意图
- [ ] 识别约束条件
- [ ] 将发现记录在 findings.md 中
- **状态：** in_progress

### 阶段 2：方案设计与架构
- [ ] 定义技术方案
- [ ] 创建项目结构
- **状态：** pending

### 阶段 3：功能实现
- [ ] 逐步执行计划
- [ ] 编写代码
- **状态：** pending

### 阶段 4：测试与验证
- [ ] 验证需求已满足
- [ ] 记录测试结果
- **状态：** pending

### 阶段 5：交付与回顾
- [ ] 审查输出
- [ ] 交付给用户
- **状态：** pending

## 决策记录
| 决策 | 理由 |
|----------|-----------|

## 遇到的错误
| 错误 | 解决方案 |
|-------|------------|
EOF
    echo "已创建 task_plan.md"
else
    echo "task_plan.md 已存在，跳过"
fi

# 创建 findings.md
if [ ! -f "findings.md" ]; then
    cat > findings.md << 'EOF'
# 调研发现与决策 (Findings & Decisions)

## 需求项
- 

## 研究发现
- 

## 技术决策
| 决策 | 理由 |
|----------|-----------|

## 遇到的问题
| 问题 | 解决方案 |
|-------|------------|

## 资源链接
- 
EOF
    echo "已创建 findings.md"
else
    echo "findings.md 已存在，跳过"
fi

# 创建 progress.md
if [ ! -f "progress.md" ]; then
    cat > progress.md << EOF
# 进度日志 (Progress Log)

## 会话日期：$DATE

### 当前状态
- **阶段：** 1 - 需求分析与调研
- **开始时间：** $DATE

### 采取的行动
- 

### 测试结果
| 测试项 | 预期结果 | 实际结果 | 状态 |
|------|----------|--------|--------|

### 错误详志
| 错误类型 | 解决方案 |
|-----------|-----------|
EOF
    echo "已创建 progress.md"
else
    echo "progress.md 已存在，跳过"
fi

echo ""
echo "规划文件初始化完成！"
echo "已生成：task_plan.md, findings.md, progress.md"
