"""CTF 脚本工具注册表，按分类索引解题脚本"""
import os
import glob

# 脚本分类映射
CATEGORY_MAP = {
    "crypto": ["RSA", "DES", "AES", "md5", "Base", "rot", "维吉尼亚", "凯撒", "四方密码",
               "Nihilist", "toy密码", "进制", "hex"],
    "stego": ["steghide", "频域盲水印", "RGB转图片", "图片爆破宽高", "TTL隐写", "字节转二维码"],
    "traffic": ["usb流量", "流量数据提取", "曼彻斯特编码", "tshark"],
    "web": ["双参数爆破", "日志匹配", "sqlmap"],
    "misc": ["CRC32", "批量解压", "去重", "文本转gbk", "emoji", "Brainfuck",
             "Picke序列化", "遍历读取压缩包"],
    "reverse": ["reverse", "xor", "二进制"],
}


class ScriptRegistry:
    """CTF 脚本工具注册表"""

    def __init__(self, scripts_dir: str = "data/scripts/ctf_tools"):
        self.scripts_dir = scripts_dir

    def _categorize(self, dir_name: str) -> str:
        for cat, keywords in CATEGORY_MAP.items():
            if any(kw.lower() in dir_name.lower() for kw in keywords):
                return cat
        return "misc"

    def list_scripts(self, category: str = None) -> list[dict]:
        """列出所有可用脚本

        Args:
            category: 过滤分类 (crypto/stego/traffic/web/misc/reverse)

        Returns:
            脚本目录列表，每个包含 name/category/path/scripts/script_count
        """
        if not os.path.exists(self.scripts_dir):
            return []

        results = []
        for entry in os.scandir(self.scripts_dir):
            if not entry.is_dir() or entry.name.startswith('.'):
                continue

            cat = self._categorize(entry.name)
            if category and cat != category:
                continue

            py_files = glob.glob(os.path.join(entry.path, "**/*.py"), recursive=True)

            results.append({
                "name": entry.name,
                "category": cat,
                "path": entry.path,
                "scripts": [os.path.relpath(f, self.scripts_dir) for f in py_files],
                "script_count": len(py_files),
            })

        return sorted(results, key=lambda x: x["name"])

    def find_script(self, keyword: str) -> dict | None:
        """按关键词查找脚本

        Args:
            keyword: 搜索关键词（如 "RSA"、"CRC32"、"USB流量"）

        Returns:
            匹配的脚本信息，包含 name/category/path/all_scripts
        """
        all_scripts = self.list_scripts()
        keyword_lower = keyword.lower()

        for script in all_scripts:
            if keyword_lower in script["name"].lower():
                if script["scripts"]:
                    return {
                        "name": script["name"],
                        "category": script["category"],
                        "path": os.path.join(self.scripts_dir, script["scripts"][0]),
                        "all_scripts": script["scripts"],
                    }
        return None
