from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send messages to LLM and get response."""
        pass
