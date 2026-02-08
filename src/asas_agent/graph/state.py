from typing import TypedDict, Optional, Any, Dict

class AgentState(TypedDict):
    """The state of the agent workflow."""
    user_input: str
    platform_url: Optional[str]
    platform_token: Optional[str]
    challenge_id: Optional[str]
    task_understanding: Optional[str]
    planned_tool: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    final_answer: Optional[str]
    error: Optional[str]
    task_history: Optional[list] # List of tried tools and results
    pending_tasks: Optional[list] # List of alternative paths
