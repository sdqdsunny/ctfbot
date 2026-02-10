from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from langchain_core.tools import tool

class AgentResult(BaseModel):
    """Standardized result from a specialized agent."""
    status: str = Field(..., description="success, failure, or indeterminate")
    flag: Optional[str] = Field(None, description="The flag if found")
    reasoning: str = Field(..., description="Summary of reasoning and actions taken")
    artifacts: List[str] = Field(default_factory=list, description="Paths to extracted files or data")
    error: Optional[str] = Field(None, description="Error message if any")

@tool
async def dispatch_to_agent(agent_type: str, task: str, platform_context: Dict[str, Any]) -> str:
    """
    Dispatch a task to a specialized agent.
    
    Args:
        agent_type: One of 'crypto', 'web', 'reverse', 'recon', 'writeup', 'memory'
        task: Detailed description of the task to perform
        platform_context: Dictionary containing platform_url, platform_token, and challenge_id
        
    Returns:
        A JSON string containing the AgentResult.
    """
    # This is a placeholder for the actual dispatch logic which will be implemented in Phase 3
    # For now, it returns a simulated result for testing the Orchestrator.
    return f"Dispatching to {agent_type} agent: {task}. Context: {platform_context}"
