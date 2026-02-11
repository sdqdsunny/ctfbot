#!/bin/bash
# 检查 task_plan.md 中的所有阶段是否已完成 (Chinese Version)
# 完成返回 0，未完成返回 1
# 由 Stop hook 调用以验证任务完成情况

PLAN_FILE="${1:-task_plan.md}"

if [ ! -f "$PLAN_FILE" ]; then
    echo "错误：找不到 $PLAN_FILE"
    echo "没有任务计划，无法验证完成情况。"
    exit 1
fi

echo "=== 任务完成情况检查 ==="
echo ""

# 按状态计算阶段数量 (使用中文关键字)
TOTAL=$(grep -c "### 阶段" "$PLAN_FILE" || true)
COMPLETE=$(grep -cF "**状态：** complete" "$PLAN_FILE" || true)
IN_PROGRESS=$(grep -cF "**状态：** in_progress" "$PLAN_FILE" || true)
PENDING=$(grep -cF "**状态：** pending" "$PLAN_FILE" || true)

# 默认值为 0
: "${TOTAL:=0}"
: "${COMPLETE:=0}"
: "${IN_PROGRESS:=0}"
: "${PENDING:=0}"

echo "总阶段数：   $TOTAL"
echo "已完成：     $COMPLETE"
echo "进行中：     $IN_PROGRESS"
echo "待处理：     $PENDING"
echo ""

# 检查是否全部完成
if [ "$COMPLETE" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
    echo "所有阶段已完成！"
    exit 0
else
    echo "任务尚未完成。"
    echo ""
    echo "在所有阶段完成标记为 'complete' 之前，请不要停止。"
    exit 1
fi
