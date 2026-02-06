# Digital CTFer - ASAS Core MCP Server

CTF 自动解题智能体系统的核心 MCP 服务器，基于 Model Context Protocol (MCP) 构建。

## 🛠️ 当前能力 (Capabilities)

本项目目前实现了以下 CTF 辅助工具：

| 类别 | 工具名称 | 描述 |
|------|----------|------|
| **Recon** | `recon_scan` | 基础网络端口扫描 |
| **Crypto** | `crypto_decode` | 多格式解码 (Base64, Hex, URL) |
| **Misc** | `misc_identify_file` | 基于文件头(Magic Bytes)识别文件类型 |
| **Reverse**| `reverse_extract_strings`| 从二进制数据中提取可打印字符串 |

## 🚀 快速集成指南 (Claude Desktop)

要让 Claude Desktop 使用此工具集，请按照以下步骤操作：

### 1. 准备环境

确保你已经安装了依赖并使其可执行：

```bash
chmod +x scripts/start_mcp_server.sh
```

### 2. 编辑配置文件

打开 Claude Desktop 的配置文件：

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

如果文件不存在，请创建它。

### 3. 添加服务器配置

将以下内容添加到配置文件中（请确保 `command` 路径是绝对路径）：

```json
{
  "mcpServers": {
    "digital-ctfer": {
      "command": "/Users/guoshuguang/my-project/antigravity/digital-ctfer/scripts/start_mcp_server.sh",
      "args": []
    }
  }
}
```

> **注意**: 如果你移动了项目文件夹，请务必更新上面的路径。

### 4. 重启 Claude

完全退出并重新打开 Claude Desktop。你应该能看到一个 "🔌" 图标或在对话中看到已连接的工具。

## 🐳 Docker 部署

如果你偏好容器化运行（HTTP 模式）：

```bash
# 构建镜像
docker build -t asas-core-mcp:latest .

# 启动服务
docker-compose up -d
```

服务将在 `http://localhost:8000` 启动。

## 📦 开发与测试

```bash
# 安装依赖
pip install poetry
poetry install

# 运行测试
poetry run pytest
```
