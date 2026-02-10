from langgraph.graph import MessagesState
from typing import Optional

class AgentState(MessagesState):
    """v2.0 ReAct Agent State - inherits messages from MessagesState"""
    platform_url: Optional[str]
    platform_token: Optional[str]
    challenge_id: Optional[str]

