"""ASAS Core MCP —— 能力引擎 / 工具服务器。

版本号与 ``asas_agent`` 同源：仓库根 ``pyproject.toml`` 是唯一权威，
本字面量是副本，由 ``scripts/check_version.py`` 强制一致。

这里不从 ``asas_agent`` 导入 ``__version__``——两个包是分层关系，
asas_mcp 是更底层的工具服务器，反向依赖会把依赖方向弄反。
"""
__version__ = "0.8.0"
