from typing import TypedDict, Optional, Any, Dict

class AgentState(TypedDict):
    """The state of the agent workflow."""
    user_input: str
    task_understanding: Optional[str]
    planned_tool: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[str]
    final_answer: Optional[str]
    error: Optional[str]
