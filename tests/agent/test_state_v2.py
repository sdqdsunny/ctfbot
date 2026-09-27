from asas_agent.graph.state import AgentState
from langgraph.graph import MessagesState

def test_agent_state_inheritance():
    # Verify AgentState inherits from MessagesState (or compatible structure)
    # v2 state should primarily use 'messages'
    state = AgentState(messages=[], platform_url="http://test.com")
    assert "messages" in state
    assert state["platform_url"] == "http://test.com"
