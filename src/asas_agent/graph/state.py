from langgraph.graph import MessagesState
from typing import Optional, Any, Dict, List

class AgentState(MessagesState):
    """v2.0 ReAct Agent State - inherits messages from MessagesState"""
    # v2 fields (platform context)
    platform_url: Optional[str]
    platform_token: Optional[str]
    challenge_id: Optional[str]
    
    # v3 multi-agent fields
    challenges: Optional[list]  # List of challenge objects from platform
    agent_results: Optional[Dict[str, Any]]  # {challenge_id: AgentResult}
    fact_store: Dict[str, Dict[str, Any]] = {
        "recon": {}, "web": {}, "crypto": {}, "reverse": {}, "common": {}
    }
    current_agent: Optional[str]
    retry_count: int = 0  # v4 Reflection loop counter
    
    # v5 verification loop fields
    extracted_flags: List[str] = []              # 已提取的 flag 列表
    verification_status: Optional[str] = None    # None / "l1_passed" / "l2_needs_poc" / "l3_verified" / "failed"
    poc_attempts: int = 0                        # PoC 验证尝试次数
    
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
