from langgraph.graph import MessagesState
from typing import Optional, Any, Dict

class AgentState(MessagesState):
    """v2.0 ReAct Agent State - inherits messages from MessagesState"""
    # v2 fields (platform context)
    platform_url: Optional[str]
    platform_token: Optional[str]
    challenge_id: Optional[str]
    
    # v3 multi-agent fields
    challenges: Optional[list]  # List of challenge objects from platform
    agent_results: Optional[Dict[str, Any]]  # {challenge_id: AgentResult}
    current_agent: Optional[str]
    retry_count: int = 0  # v4 Reflection loop counter
    
    # v1 compatibility fields (will be deprecated)
    user_input: Optional[str]
    task_understanding: Optional[str]
    planned_tool: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    final_answer: Optional[str]
    error: Optional[str]
    task_history: Optional[list]
    pending_tasks: Optional[list]
