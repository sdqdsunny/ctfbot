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
