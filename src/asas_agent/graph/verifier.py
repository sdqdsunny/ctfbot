"""验证闭环模块：Flag 提取 + PoC 验证"""
import re
from typing import Optional


# 支持的 flag 前缀（小写匹配）
_FLAG_PREFIXES = [
    "flag",
    "ctf",
    "ctfshow",
    "hctf",
    "sctf",
    "hitcon",
    "bctf",
    "qwb",       # 强网杯
    "dasctf",
    "moectf",
    "iscc",
]

# 构建正则：(flag|ctf|ctfshow|...)\{[^}]+\}
_PREFIX_PATTERN = "|".join(re.escape(p) for p in _FLAG_PREFIXES)
_FLAG_RE = re.compile(
    rf"({_PREFIX_PATTERN})\{{([^}}]+)\}}",
    re.IGNORECASE,
)


class FlagExtractor:
    """从任意文本中提取 CTF flag。

    支持多种前缀格式，大小写不敏感，自动去重。
    """

    def __init__(self, extra_prefixes: Optional[list[str]] = None):
        if extra_prefixes:
            all_prefixes = _FLAG_PREFIXES + extra_prefixes
            prefix_pattern = "|".join(re.escape(p) for p in all_prefixes)
            self._re = re.compile(
                rf"({prefix_pattern})\{{([^}}]+)\}}",
                re.IGNORECASE,
            )
        else:
            self._re = _FLAG_RE

    def extract(self, text: str) -> list[str]:
        """从文本中提取所有 flag，返回去重后的列表。"""
        matches = self._re.findall(text)
        # findall 返回 [(prefix, content), ...]，重建完整 flag
        seen: set[str] = set()
        result: list[str] = []
        for prefix, content in matches:
            full_flag = f"{prefix}{{{content}}}"
            if full_flag not in seen:
                seen.add(full_flag)
                result.append(full_flag)
        return result

    def has_flag(self, text: str) -> bool:
        """快速检查文本中是否包含 flag。"""
        return bool(self._re.search(text))


# 模块级单例，方便全局使用
flag_extractor = FlagExtractor()


def build_reflection_prompt(retry_count: int, content: str, scenario: str) -> str:
    """构造不同场景下的 reflection prompt。
    
    Args:
        retry_count: 当前重试次数（从 0 开始）
        content: 上一步工具输出内容（截断后）
        scenario: "error" / "progress" / "stale"
    
    Returns:
        引导 LLM 反思的 prompt 字符串
    """
    current_attempt = retry_count + 1
    
    if scenario == "error":
        return (
            f"反思时刻 (第 {current_attempt}/3 次尝试)：\n"
            f"上一步工具调用返回了错误。\n"
            f"错误信息: {content[:500]}\n\n"
            "请分析失败原因，并生成一个新的策略。你可以尝试：\n"
            "1. 检查参数是否正确（URL、端口、路径）。\n"
            "2. 换一个工具或方法。\n"
            "3. 使用 `memory_query` 查找类似问题的解决办法。\n"
            "4. 使用 `kali_exec` 手工执行命令探查。\n\n"
            "请直接调用工具，不要只是分析。"
        )
    
    elif scenario == "progress":
        return (
            f"进展分析 (第 {current_attempt}/3 次尝试)：\n"
            f"上一步工具调用成功返回了结果，但尚未找到 flag。\n"
            f"工具输出: {content[:500]}\n\n"
            "请分析当前进展，并决定下一步：\n"
            "1. 如果发现了数据库/表/文件 → 继续深入提取数据。\n"
            "2. 如果输出中有疑似 flag 的编码内容 → 尝试解码。\n"
            "3. 如果当前攻击面已穷尽 → 切换到其他方向。\n\n"
            "目标：找到 flag{...} 格式的字符串。请直接调用工具。"
        )
    
    elif scenario == "stale":
        return (
            f"停滞检测 (第 {current_attempt}/3 次尝试)：\n"
            f"已多次成功执行工具但仍未找到 flag。\n"
            f"最近输出: {content[:500]}\n\n"
            "建议采取以下措施之一：\n"
            "1. 编写一个独立的 PoC 脚本验证之前的发现。\n"
            "   使用 `sandbox_execute(code='import requests; ...')` 在沙箱中运行。\n"
            "2. 回顾之前的所有发现，检查是否遗漏了关键信息。\n"
            "3. 使用 `search_writeups` 搜索类似题目的 WriteUp。\n\n"
            "请直接调用工具，不要重复之前已失败的尝试。"
        )
    
    # 兜底
    return (
        f"第 {current_attempt}/3 次尝试：\n"
        f"当前输出: {content[:300]}\n"
        "请决定下一步行动并调用工具。"
    )
