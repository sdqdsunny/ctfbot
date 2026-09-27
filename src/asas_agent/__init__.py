"""ASAS Agent —— 多智能体决策层。

版本号的唯一权威是仓库根的 ``pyproject.toml``（README 徽章也指向它）。
本文件里的字面量是它的副本，由 ``scripts/check_version.py`` 强制保持一致，
CI 与本地 ``pytest`` 都会盯着——本次修复的起因正是同一个版本号被抄在 9 处，
各自漂移成了 0.6.0 / 0.7.0 / 0.1.0 / 1.0.0，连对外 /health 报的都不是真版本。

故意不在这里查 importlib.metadata：那读的是"已安装的 dist-info"，
而本项目开发态直接从源码树跑（PYTHONPATH=src，见 README），
装没装、装的是哪个版本都与当前源码无关——本地 dist-info 实测停在 0.6.0，
用它反倒会把版本号报错。
"""
__version__ = "0.8.0"
