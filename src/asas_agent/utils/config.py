import yaml
import os
from typing import Any, Dict, Optional

class ConfigLoader:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def load_config(self, config_path: str = "v3_config.yaml") -> Dict[str, Any]:
        """Load YAML configuration file."""
        if self._config is not None:
            return self._config

        if not os.path.exists(config_path):
            # Fallback to absolute path or example
            potential_paths = [
                config_path,
                os.path.join(os.getcwd(), config_path),
                "/Users/guoshuguang/my-project/antigravity/ctfbot/v3_config.yaml"
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    config_path = p
                    break
            else:
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

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
