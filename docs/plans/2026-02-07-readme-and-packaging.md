# CTF-ASAS Clean-Up & Packaging Plan

## 1. README.md 编写 (README.md Writing)

编写一份高质量、结构化的 README.md，包含以下模块：

- **项目简介**: 定位、核心价值（Agent-native CTF solver）。
- **架构描述**: 结合 ASAS Agent MVP 设计，说明决策层与能力层的解耦。
- **快速开始**: 环境搭建 (Poetry)、API 配置、运行示例。
- **功能特性**: 目前 MVP 已实现的功能（Crypto, Scan, Identification 等）。
- **开发路线**: 未来计划 (Multi-step tasks, RAG integration 等)。

## 2. 版本号更新 (Version Update)

将 `pyproject.toml` 中的版本号从 `0.1.0` 更新为 `1.0.0`。

## 3. 代码打包 (Executable Packaging)

使用 PyInstaller 将 `asas_agent` 打包为独立可执行程序：

- **目标文件**: `src/asas_agent/__main__.py`
- **打包参数**: `--onefile`, `--name ctfbot`, 包含必要的资源文件。
- **环境**: 确保在当前 `.venv` 下执行。

## 4. 验证与交付 (Verification & Delivery)

- 验证打包后的程序在本地可正常执行。
- 确认 README.md 内容准确、排版规范。
- 提交所有更改到 Git。

---
Implemented Plan in Chinese as requested.
