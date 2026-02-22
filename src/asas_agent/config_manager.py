import json
import os
import base64
from typing import Dict, Optional
import logging

logger = logging.getLogger("config_manager")

class ConfigManager:
    """管理 API Keys 和其他配置的持久化。目前使用简单的 base64 混淆作为占位，后续可升级为真正的加密。"""
    
    def __init__(self, config_path: str = "config/providers.json"):
        self.config_path = config_path
        self.providers: Dict[str, Dict] = {
            "openai": {"apiKey": "", "model": "gpt-4o"},
            "deepseek": {"apiKey": "", "model": "deepseek-chat"},
            "claude": {"apiKey": "", "model": "claude-3-5-sonnet-latest"},
        }
        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self):
        directory = os.path.dirname(self.config_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _obfuscate(self, text: str) -> str:
        if not text: return ""
        return base64.b64encode(text.encode()).decode()

    def _deobfuscate(self, text: str) -> str:
        if not text: return ""
        try:
            return base64.b64decode(text.encode()).decode()
        except Exception:
            return ""

    def save(self):
        try:
            # 在保存前对 apiKey 进行混淆
            data_to_save = {}
            for p_id, p_data in self.providers.items():
                data_to_save[p_id] = {
                    **p_data,
                    "apiKey": self._obfuscate(p_data.get("apiKey", ""))
                }
            
            with open(self.config_path, "w") as f:
                json.dump(data_to_save, f, indent=4)
            logger.info(f"Config saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def load(self):
        if not os.path.exists(self.config_path):
            logger.info("No existing config found, using defaults.")
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                for p_id, p_data in data.items():
                    if p_id in self.providers:
                        self.providers[p_id] = {
                            **p_data,
                            "apiKey": self._deobfuscate(p_data.get("apiKey", ""))
                        }
            logger.info("Config loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def update_provider(self, provider_id: str, data: Dict):
        if provider_id in self.providers:
            self.providers[provider_id].update(data)
            self.save()
            return True
        return False

    def get_api_key(self, provider_id: str) -> Optional[str]:
        provider = self.providers.get(provider_id)
        return provider.get("apiKey") if provider else None

# 单例模式
config_manager = ConfigManager()
