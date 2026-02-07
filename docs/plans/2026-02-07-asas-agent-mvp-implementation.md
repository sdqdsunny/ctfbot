# ASAS Agent MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the ASAS Agent MVP as a standalone service that orchestrates CTF tasks using LangGraph and communicates with tools via MCP protocol.

**Architecture:**

- **Service:** `asas-agent` (standalone Python package)
- **Core:** LangGraph state machine for task orchestration
- **Integration:** MCP Client for tool execution, Abstract LLM Layer for intelligence
- **Pattern:** TDD with Pytest

**Tech Stack:** Python 3.10+, LangGraph, Anthropic SDK, MCP SDK, Pytest, Asyncio

---

### Task 1: Project Scaffolding & Dependency Setup

**Files:**

- Modify: `pyproject.toml`
- Create: `src/asas_agent/__init__.py`
- Create: `src/asas_agent/__main__.py`
- Create: `tests/agent/__init__.py`
- Create: `tests/agent/test_version.py`

**Step 1: Update Dependencies**

**pyproject.toml** (Add to existing or update)

```toml
[tool.poetry.dependencies]
python = "^3.10"
langgraph = "^0.2.0"
anthropic = "^0.40.0"
mcp = "^1.2.0"
click = "^8.1.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
```

**Step 2: Install Dependencies**

Run: `source .venv/bin/activate && poetry install`
Expected: Success

**Step 3: Create Directory Structure**

Run: `mkdir -p src/asas_agent/graph src/asas_agent/llm src/asas_agent/mcp_client src/asas_agent/models tests/agent`

**Step 4: Write failing test for version**

**tests/agent/test_version.py**

```python
from asas_agent import __version__

def test_version():
    assert __version__ == "0.1.0"
```

**Step 5: Run test to verify it fails**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_version.py -v`
Expected: FAIL (ImportError or version mismatch)

**Step 6: Write minimal implementation**

**src/asas_agent/**init**.py**

```python
__version__ = "0.1.0"
```

**Step 7: Run test to verify it passes**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_version.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add pyproject.toml src/asas_agent/ tests/agent/
git commit -m "chore: init agent project structure and dependencies"
```

---

### Task 2: LLM Abstraction Layer (Base & Mock)

**Files:**

- Create: `src/asas_agent/llm/base.py`
- Create: `src/asas_agent/llm/mock.py`
- Create: `src/asas_agent/llm/__init__.py`
- Create: `tests/agent/test_llm.py`

**Step 1: Write failing test for Mock LLM**

**tests/agent/test_llm.py**

```python
import pytest
from asas_agent.llm.mock import MockLLM

def test_mock_llm_crypto_decode():
    llm = MockLLM()
    messages = [{"role": "user", "content": "请解码这段 Base64: SGVsbG8="}]
    response = llm.chat(messages)
    assert "crypto_decode" in response

def test_mock_llm_recon_scan():
    llm = MockLLM()
    messages = [{"role": "user", "content": "扫描 IP 127.0.0.1"}]
    response = llm.chat(messages)
    assert "recon_scan" in response

def test_mock_llm_unknown():
    llm = MockLLM()
    messages = [{"role": "user", "content": "你好"}]
    response = llm.chat(messages)
    assert "unknown" in response
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_llm.py -v`
Expected: FAIL (ModuleNotFoundError)

**Step 3: Implement Base LLM Class**

**src/asas_agent/llm/base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send messages to LLM and get response."""
        pass
```

**Step 4: Implement Mock LLM**

**src/asas_agent/llm/mock.py**

```python
from typing import List, Dict
from .base import LLMProvider

class MockLLM(LLMProvider):
    """Mock LLM for development and testing."""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        user_msg = messages[-1]["content"].lower()
        
        # Simple rule-based matching
        if "base64" in user_msg or "解码" in user_msg or "decode" in user_msg:
            return "crypto_decode"
        elif "扫描" in user_msg or "scan" in user_msg:
            return "recon_scan"
        elif "文件" in user_msg or "file" in user_msg:
            return "misc_identify_file"
        elif "字符串" in user_msg or "string" in user_msg:
            return "reverse_extract_strings"
        
        return "unknown"
```

**src/asas_agent/llm/**init**.py**

```python
from .base import LLMProvider
from .mock import MockLLM
```

**Step 5: Run test to verify it passes**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_llm.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/asas_agent/llm/ tests/agent/test_llm.py
git commit -m "feat: implement LLM abstraction and Mock provider"
```

---

### Task 3: Claude LLM Provider

**Files:**

- Create: `src/asas_agent/llm/claude.py`
- Modify: `src/asas_agent/llm/__init__.py`
- Modify: `tests/agent/test_llm.py`

**Step 1: Write testing (Mocking Anthropic API)**

**tests/agent/test_llm.py** (Append)

```python
from unittest.mock import MagicMock, patch
from asas_agent.llm.claude import ClaudeLLM

def test_claude_llm_call():
    with patch("anthropic.Anthropic") as MockAnthropic:
        # User auth check
        mock_client = MockAnthropic.return_value
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response from Claude")]
        mock_client.messages.create.return_value = mock_message
        
        llm = ClaudeLLM(api_key="fake-key")
        messages = [{"role": "user", "content": "Hello"}]
        response = llm.chat(messages)
        
        assert response == "Response from Claude"
        mock_client.messages.create.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_llm.py::test_claude_llm_call -v`
Expected: FAIL (ModuleNotFoundError)

**Step 3: Implement Claude LLM**

**src/asas_agent/llm/claude.py**

```python
from typing import List, Dict
import anthropic
from .base import LLMProvider

class ClaudeLLM(LLMProvider):
    """Anthropic Claude LLM Provider."""
    
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=messages
        )
        return response.content[0].text
```

**src/asas_agent/llm/**init**.py** (Update)

```python
from .base import LLMProvider
from .mock import MockLLM
from .claude import ClaudeLLM
```

**Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_llm.py::test_claude_llm_call -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_agent/llm/claude.py src/asas_agent/llm/__init__.py tests/agent/test_llm.py
git commit -m "feat: implement Claude LLM provider"
```

---

### Task 4: MCP Client Wrapper

**Files:**

- Create: `src/asas_agent/mcp_client/client.py`
- Create: `src/asas_agent/mcp_client/__init__.py`
- Create: `tests/agent/test_mcp_client.py`

**Step 1: Write failing test (Async)**

**tests/agent/test_mcp_client.py**

```python
import pytest
from unittest.mock import AsyncMock, patch
from asas_agent.mcp_client.client import MCPToolClient

@pytest.mark.asyncio
async def test_call_tool():
    # We mock the stdio_client context manager and session
    with patch("asas_agent.mcp_client.client.stdio_client") as mock_stdio:
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        # Mock result structure
        mock_result = AsyncMock()
        mock_result.content = [AsyncMock(text="Tool Output")]
        mock_session.call_tool.return_value = mock_result
        
        # Setup context managers
        mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
        
        with patch("asas_agent.mcp_client.client.ClientSession") as MockSession:
            MockSession.return_value.__aenter__.return_value = mock_session
            
            client = MCPToolClient()
            result = await client.call_tool("test_tool", {"arg": "val"})
            
            assert result == "Tool Output"
            mock_session.call_tool.assert_called_with("test_tool", {"arg": "val"})
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_mcp_client.py -v`
Expected: FAIL

**Step 3: Implement MCP Client**

**src/asas_agent/mcp_client/client.py**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

class MCPToolClient:
    """Client for calling MCP tools."""
    
    def __init__(self):
        # By default, connect to the local asas_mcp module
        # We need to run it as a python module
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        
        self.server_params = StdioServerParameters(
            command=sys.executable, # Use current python interpreter
            args=["-m", "asas_mcp"],
            env={**os.environ, "PYTHONPATH": f"{project_root}/src"}
        )
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool on the MCP server."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                # Assuming text result for now
                if hasattr(result, 'content') and result.content:
                    return result.content[0].text
                return str(result)

    async def list_tools(self) -> list:
        """List available tools."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools
```

**src/asas_agent/mcp_client/**init**.py**

```python
from .client import MCPToolClient
```

**Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_mcp_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_agent/mcp_client/ tests/agent/test_mcp_client.py
git commit -m "feat: implement MCP client wrapper"
```

---

### Task 5: LangGraph State Machine (Core Logic)

**Files:**

- Create: `src/asas_agent/graph/state.py`
- Create: `src/asas_agent/graph/nodes.py`
- Create: `src/asas_agent/graph/workflow.py`
- Create: `src/asas_agent/graph/__init__.py`
- Create: `tests/agent/test_graph.py`

**Step 1: Define State**

**src/asas_agent/graph/state.py**

```python
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
```

**Step 2: Implement Nodes (Mock Logic first)**

**src/asas_agent/graph/nodes.py**

```python
from .state import AgentState
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

class AgentNodes:
    def __init__(self, llm: LLMProvider, mcp_client: MCPToolClient):
        self.llm = llm
        self.mcp_client = mcp_client

    async def understand_task(self, state: AgentState) -> AgentState:
        """Determine intent using LLM."""
        messages = [{"role": "user", "content": state["user_input"]}]
        understanding = self.llm.chat(messages)
        return {"task_understanding": understanding}

    async def plan_actions(self, state: AgentState) -> AgentState:
        """Map understanding to tool args (Simplified for MVP)."""
        intent = state.get("task_understanding", "")
        
        # Simple extraction for MVP - Replace with LLM extraction later
        user_input = state["user_input"]
        
        if intent == "crypto_decode":
            # Extract content after colon or just use input if testing
            content = user_input.split(":")[-1].strip() if ":" in user_input else "SGVsbG8="
            return {
                "planned_tool": "crypto_decode",
                "tool_args": {"content": content, "method": "base64"}
            }
        elif intent == "recon_scan":
            target = user_input.split("IP")[-1].strip() if "IP" in user_input else "127.0.0.1"
            return {
                "planned_tool": "recon_scan", 
                "tool_args": {"target": target, "ports": "80"}
            }
            
        return {"error": "Unknown intent"}

    async def execute_tool(self, state: AgentState) -> AgentState:
        """Execute the planned tool."""
        if state.get("error"):
            return state
            
        tool = state["planned_tool"]
        args = state["tool_args"]
        
        try:
            result = await self.mcp_client.call_tool(tool, args)
            return {"tool_result": result}
        except Exception as e:
            return {"error": str(e)}

    async def format_result(self, state: AgentState) -> AgentState:
        """Format final answer."""
        if state.get("error"):
            return {"final_answer": f"Error: {state['error']}"}
        
        return {"final_answer": str(state["tool_result"]).strip()}
```

**Step 3: Build Workflow**

**src/asas_agent/graph/workflow.py**

```python
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import AgentNodes
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

def create_agent_graph(llm: LLMProvider):
    mcp_client = MCPToolClient()
    nodes = AgentNodes(llm, mcp_client)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("understand", nodes.understand_task)
    workflow.add_node("plan", nodes.plan_actions)
    workflow.add_node("execute", nodes.execute_tool)
    workflow.add_node("format", nodes.format_result)
    
    workflow.set_entry_point("understand")
    
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "format")
    workflow.add_edge("format", END)
    
    return workflow.compile()
```

**Step 4: Commit**

```bash
git add src/asas_agent/graph/
git commit -m "feat: implement LangGraph state machine"
```

---

### Task 6: CLI Entry Point & Integration Test

**Files:**

- Create: `src/asas_agent/__main__.py`
- Modify: `pyproject.toml`
- Create: `tests/agent/test_integration.py`

**Step 1: Implement CLI**

**src/asas_agent/**main**.py**

```python
import asyncio
import click
import os
from dotenv import load_dotenv

from .graph.workflow import create_agent_graph
from .llm.mock import MockLLM
from .llm.claude import ClaudeLLM

load_dotenv()

@click.command()
@click.argument('input_text')
@click.option('--llm', type=click.Choice(['mock', 'claude']), default='mock', help='LLM provider to use')
@click.option('--api-key', help='Anthropic API Key', envvar='ANTHROPIC_API_KEY')
def main(input_text, llm, api_key):
    """ASAS Agent CLI - Execute CTF tasks."""
    
    print(f"🤖 ASAS Agent ({llm.capitalize()} Mode)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Select LLM
    if llm == 'claude':
        if not api_key:
            click.echo("Error: API Key required for Claude mode", err=True)
            return
        llm_provider = ClaudeLLM(api_key=api_key)
    else:
        llm_provider = MockLLM()
    
    # Run Graph
    app = create_agent_graph(llm_provider)
    
    inputs = {"user_input": input_text}
    
    async def run():
        result = await app.ainvoke(inputs)
        
        print(f"📝 理解: {result.get('task_understanding')}")
        print(f"🔧 规划: {result.get('planned_tool')} {result.get('tool_args')}")
        print(f"⚙️  结果: {result.get('tool_result')}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎯 最终答案: {result.get('final_answer')}")

    asyncio.run(run())

if __name__ == '__main__':
    main()
```

**Step 2: Integration Test (Mock Mode)**

**tests/agent/test_integration.py**

```python
import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_end_to_end_crypto_mock():
    # Setup
    llm = MockLLM()
    app = create_agent_graph(llm)
    
    # Exec
    # Mock LLM knows "decode" maps to crypto_decode
    # Nodes.plan_actions knows to extract content after colon
    inputs = {"user_input": "Please decode: SGVsbG8gV29ybGQ="}
    result = await app.ainvoke(inputs)
    
    # Verify
    assert result["task_understanding"] == "crypto_decode"
    assert result["planned_tool"] == "crypto_decode"
    assert result["tool_args"]["content"] == "SGVsbG8gV29ybGQ="
    # This proves we actually called the running MCP server!
    assert "Hello World" in result["final_answer"]
```

**Step 3: Run Integration Test**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/agent/test_integration.py -v`
Expected: PASS

**Step 4: Manual CLI Test**

Run: `source .venv/bin/activate && python -m asas_agent "decode: SGVsbG8gV29ybGQ="`
Expected: Output showing "Hello World"

**Step 5: Commit**

```bash
git add src/asas_agent/__main__.py tests/agent/test_integration.py
git commit -m "feat: implement CLI and integration tests"
```

---
