"""LangChain-compatible Claude LLM wrapper for v2 ReAct architecture"""
from langchain_anthropic import ChatAnthropic
import os


def create_langchain_claude(api_key: str = None, model: str = None) -> ChatAnthropic:
    """
    Create a LangChain-compatible Claude LLM instance.
    
    Args:
        api_key: Anthropic API key (optional, will use env var if not provided)
        model: Model name (optional, defaults to claude-3-5-sonnet-20241022)
        
    Returns:
        ChatAnthropic instance ready for use with LangGraph
    """
    # Support for local LLM (e.g., LM Studio, Ollama) providing an Anthropic-compatible API
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    # If connecting locally, map ANTHROPIC_AUTH_TOKEN to api_key if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    
    # Local models might not need a real key, but the SDK requires a string
    if base_url and not api_key:
        api_key = "dummy-key-for-local-model"
    
    # Use the requested model or default
    if not model:
        model = os.environ.get("ASAS_MODEL_NAME", "claude-3-5-sonnet-20241022")
    
    # Create ChatAnthropic instance
    llm = ChatAnthropic(
        api_key=api_key,
        model=model,
        base_url=base_url,
        temperature=0  # Deterministic for CTF solving
    )
    
    return llm
