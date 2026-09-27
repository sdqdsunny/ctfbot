import yaml
import os
from typing import Any, Dict, Optional

DEFAULT_CONFIG_FILE = "v3_config.yaml"

# 仓库根目录：<root>/src/asas_agent/utils/config.py 往上四层
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ConfigNotFoundError(FileNotFoundError):
    """配置文件缺失。

    用独立类型是为了让 CLI 层能精确捕获"环境没准备好"这一类问题并给出
    干净的提示，而不必宽泛地吃掉所有 FileNotFoundError——后者可能来自
    agent 深处缺失的工具二进制，用配置的口吻报告会误导排查方向。
    """

class ConfigLoader:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载 YAML 配置。

        Args:
            config_path: 配置路径。传 None 表示使用默认的 v3_config.yaml。
                显式传入却不存在的路径会直接失败，不会回退——避免"我明明指定了
                这个文件，程序却读了别的"这种难以排查的情况。
        """
        if self._config is not None:
            return self._config

        explicit = config_path is not None
        config_path = config_path or DEFAULT_CONFIG_FILE

        if not os.path.exists(config_path):
            if explicit:
                raise ConfigNotFoundError(
                    f"指定的配置文件不存在: {config_path}\n"
                    f"  解析为绝对路径: {os.path.abspath(config_path)}\n"
                    f"  当前工作目录: {os.getcwd()}"
                )

            # 默认路径：再试一次仓库根目录（支持从子目录启动）
            candidate = os.path.join(_REPO_ROOT, config_path)
            if os.path.exists(candidate):
                config_path = candidate
            else:
                example = os.path.join(_REPO_ROOT, DEFAULT_CONFIG_FILE + ".example")
                raise ConfigNotFoundError(
                    f"未找到配置文件: {config_path}\n"
                    f"  已尝试: {os.path.abspath(config_path)}\n"
                    f"          {candidate}\n"
                    f"  当前工作目录: {os.getcwd()}\n"
                    f"\n"
                    f"  本仓库不含 v3_config.yaml（含本地配置，已被 .gitignore 忽略），\n"
                    f"  首次使用需从模板创建：\n"
                    f"\n"
                    f"      cp {DEFAULT_CONFIG_FILE}.example {DEFAULT_CONFIG_FILE}\n"
                    f"\n"
                    f"  API Key 不写在该文件里 —— 设置环境变量 DEEPSEEK_API_KEY 即可\n"
                    f"  （或写入 .env，见 README「配置 API Key」）。\n"
                    f"  模板存在: {os.path.exists(example)}\n"
                    f"  另可用 --config 指定其它配置文件。"
                )

        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)
        return self._config

    def get_agent_config(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent type."""
        config = self.load_config()
        agents_config = config.get("agents", {})
        return agents_config.get(agent_type)

    def get_orchestrator_config(self) -> Dict[str, Any]:
        """Get orchestrator configuration."""
        config = self.load_config()
        return config.get("orchestrator", {})

# Singleton instance
config_loader = ConfigLoader()
