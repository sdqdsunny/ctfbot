from typing import List, Dict
import os
import anthropic
from .base import LLMProvider

class ClaudeLLM(LLMProvider):
    """Anthropic Claude LLM Provider."""
    
    def __init__(self, api_key: str = None):
        # Support for local LLM (e.g., LM Studio, Ollama) providing an Anthropic-compatible API
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        
        # If connecting locally, map ANTHROPIC_AUTH_TOKEN to api_key if not provided
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        
        # Local models might not need a real key, but the SDK requires a string
        if base_url and not api_key:
            api_key = "dummy-key-for-local-model"

        self.client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        # Use the requested model or default. For local models, this name might be ignored or important depending on server.
        # User can override model via env var if needed, but we keep default simple for now.
        self.model = os.environ.get("ASAS_MODEL_NAME", "claude-3-5-sonnet-20241022")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=messages
        )
        return response.content[0].text
