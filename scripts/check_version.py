#!/usr/bin/env python3
"""校验全仓库声明的版本号是否一致（唯一权威：仓库根 pyproject.toml）。

背景：
    版本号曾被抄在 9 个地方，各自漂移互不相同——
    pyproject 0.6.0 / README 徽章 0.7.0 / 两个 __init__.py 1.0.0 /
    UI 三件套 0.1.0 / 对外 /health 与 MCP 根路由硬编码 0.1.0。
    结果是同一个交付物对外报出四个版本，打 tag 也无从对齐。
    本脚本把这些声明点集中起来比对，任何一处漂移都会失败。

用法：
    python scripts/check_version.py                 # 只校验一致性
    python scripts/check_version.py --tag v0.8.0    # 额外校验 tag 与版本一致
    python scripts/check_version.py --print         # 只输出版本号（供 CI 取用）

退出码：0=一致　1=不一致或读取失败
"""
import argparse
import json
import os
import re
import sys

# 仓库根：<root>/scripts/check_version.py 往上一层
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 所有声明版本号的位置。每一项是 (展示名, 相对路径, 提取方式)
_PYPROJECT = "pyproject.toml"
_AGENT_INIT = os.path.join("src", "asas_agent", "__init__.py")
_MCP_INIT = os.path.join("src", "asas_mcp", "__init__.py")
_UI_PKG = os.path.join("ui", "package.json")
_UI_TAURI = os.path.join("ui", "src-tauri", "tauri.conf.json")
_UI_CARGO = os.path.join("ui", "src-tauri", "Cargo.toml")


def _read(path: str) -> str:
    with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as f:
        return f.read()


def _from_pyproject() -> str:
    """取 [tool.poetry] 段里的 version。

    只在该段内查找，避免误抓依赖的版本号（依赖里也有大量 version = "..."）。
    """
    content = _read(_PYPROJECT)
    section = re.search(
        r"^\[tool\.poetry\]\s*$(.*?)(?=^\[)", content, re.MULTILINE | re.DOTALL
    )
    scope = section.group(1) if section else content
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', scope, re.MULTILINE)
    if not m:
        raise ValueError(f"{_PYPROJECT} 的 [tool.poetry] 段里没找到 version")
    return m.group(1)


def _from_init(path: str) -> str:
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', _read(path), re.MULTILINE)
    if not m:
        raise ValueError(f"{path} 里没找到 __version__")
    return m.group(1)


def _from_json(path: str) -> str:
    data = json.loads(_read(path))
    if "version" not in data:
        raise ValueError(f"{path} 里没有 version 字段")
    return data["version"]


def _from_cargo() -> str:
    """取 [package] 段里的 version（Cargo.toml 也有 [dependencies] version 字段）。"""
    content = _read(_UI_CARGO)
    section = re.search(
        r"^\[package\]\s*$(.*?)(?=^\[)", content, re.MULTILINE | re.DOTALL
    )
    scope = section.group(1) if section else content
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', scope, re.MULTILINE)
    if not m:
        raise ValueError(f"{_UI_CARGO} 的 [package] 段里没找到 version")
    return m.group(1)


# 声明点清单：(展示名, 提取函数)
SOURCES = [
    ("pyproject.toml", _from_pyproject),
    ("src/asas_agent/__init__.py", lambda: _from_init(_AGENT_INIT)),
    ("src/asas_mcp/__init__.py", lambda: _from_init(_MCP_INIT)),
    ("ui/package.json", lambda: _from_json(_UI_PKG)),
    ("ui/src-tauri/tauri.conf.json", lambda: _from_json(_UI_TAURI)),
    ("ui/src-tauri/Cargo.toml", _from_cargo),
]


def collect() -> dict:
    """{展示名: 版本号}；读取失败会带上原因，便于定位是哪一处坏了。"""
    found = {}
    for name, getter in SOURCES:
        try:
            found[name] = getter()
        except Exception as e:  # 读不到 = 也是必须报出来的问题
            found[name] = f"<读取失败: {e}>"
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="校验各处的版本号是否一致")
    parser.add_argument("--tag", help="额外校验该 git tag 与版本号一致（如 v0.8.0）")
    parser.add_argument("--print", dest="print_only", action="store_true",
                        help="只输出版本号，不做一致性校验")
    args = parser.parse_args()

    found = collect()
    canonical = found["pyproject.toml"]

    if args.print_only:
        print(canonical)
        return 0

    problems = []

    print(f"权威版本（{_PYPROJECT}）: {canonical}")
    for name, ver in found.items():
        mark = "✓" if ver == canonical else "✗"
        print(f"  {mark} {name}: {ver}")
        if ver != canonical:
            problems.append(f"{name} 是 {ver}，与 pyproject.toml 的 {canonical} 不一致")

    if args.tag:
        # git tag 习惯带 v 前缀，版本号本身不带；两种写法都接受
        tag_version = args.tag[1:] if args.tag.startswith("v") else args.tag
        print(f"\ngit tag: {args.tag} → 解析为版本 {tag_version}")
        if tag_version != canonical:
            problems.append(
                f"tag {args.tag} 与版本号 {canonical} 不匹配——"
                f"打这样的 tag 会构建出标签与实际内容不符的产物"
            )
        else:
            print("  ✓ 与权威版本一致")

    if problems:
        print("\n✗ 版本号不一致：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            f"\n  请把所有声明点改成同一个值（当前权威值为 {canonical}），"
            f"\n  或先改 pyproject.toml 再同步其余各处。",
            file=sys.stderr,
        )
        return 1

    print("\n✓ 所有声明点的版本号一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
