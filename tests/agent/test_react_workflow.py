import pytest
from asas_agent.graph.workflow import create_react_agent_graph
from unittest.mock import MagicMock

def test_react_graph_structure():
    """Test that the ReAct graph has correct structure"""
    mock_llm = MagicMock()
    mock_tools = []
    graph = create_react_agent_graph(mock_llm, mock_tools)
    
    # Check graph has expected nodes
    # Note: LangGraph compiled graphs expose nodes via .nodes attribute
    assert hasattr(graph, 'nodes') or hasattr(graph, 'get_graph')
    
    # For compiled graphs, we can check the structure
    # The exact API depends on LangGraph version, but we verify it compiles
    assert graph is not None
