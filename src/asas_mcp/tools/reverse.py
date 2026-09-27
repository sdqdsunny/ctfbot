import re
from typing import List

def extract_strings(data: bytes, min_length: int = 4) -> List[str]:
    """从二进制数据中提取可打印字符串"""
    # 匹配连续的可打印 ASCII 字符
    pattern = rb'[\x20-\x7e]{' + str(min_length).encode() + rb',}'
    matches = re.findall(pattern, data)
    return [m.decode('ascii') for m in matches]
