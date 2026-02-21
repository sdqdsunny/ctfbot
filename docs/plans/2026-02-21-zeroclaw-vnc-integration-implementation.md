# ZeroClaw VNC Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate ZeroClaw's MCP capabilities to interact with VMware target machines (Kali and Pentest Windows) via Browser-based VNC (NoVNC), breaking the CLI limitation.

**Architecture:** Connect to the locally-running ZeroClaw MCP endpoint. We instruct ZeroClaw's `browser_open` or `computer_use` (whichever is exposed) to automatically open the NoVNC address corresponding to the specified VM. We define a new MCP plugin tool `zeroclaw_open_vnc` within the CTF-ASAS Core MCP server that orchestrates this. It uses `vmrun` to get the VM's IP, then constructs the NoVNC URL and routes the command through the ZeroClaw MCP. Since direct ZeroClaw bridging can be complex, for the orchestrator, we simply expose `zeroclaw_open_vnc` in our existing `asas_mcp.server`, which internally launches a system process or sends an HTTP request to ZeroClaw's Gateway to open the browser.
Wait, a simpler reliable way is to let our existing `CTF-ASAS` Agent just use a newly built tool in `asas_mcp/tools/zeroclaw.py`. And in nodes/workflow, we provide intent routing.

**Tech Stack:** Python, MCP Tool Protocol, subprocess (for interacting with `zeroclaw CLI` or HTTP API).

---

### Task 1: Create ZeroClaw Tool in ASAS-Core-MCP

**Files:**

- Create: `src/asas_mcp/tools/zeroclaw.py`
- Modify: `src/asas_mcp/server.py`
- Test: `tests/mcp/test_zeroclaw_tool.py`

**Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch
from asas_mcp.tools.zeroclaw import zeroclaw_open_vnc

@pytest.mark.asyncio
async def test_zeroclaw_open_vnc_kali():
    with patch("asas_mcp.tools.zeroclaw.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "192.168.1.50\n"
        
        result = await zeroclaw_open_vnc("kali")
        
        assert "ZeroClaw browser launched" in result
        # Check if the correct NoVNC IP and port (6080) was passed
        mock_run.assert_any_call(
            ["zeroclaw", "agent", "-m", "打开浏览器访问 http://192.168.1.50:6080/vnc.html"],
            capture_output=True, text=True, check=False
        )
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/mcp/test_zeroclaw_tool.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'asas_mcp.tools.zeroclaw'"

**Step 3: Write minimal implementation**

Create `src/asas_mcp/tools/zeroclaw.py`:

```python
import subprocess

async def zeroclaw_open_vnc(vm_name: str) -> str:
    """
    Opens a NoVNC session to the specified VM using ZeroClaw's browser capabilities.
    """
    # 1. Get VM IP using vmrun (simplified mock logic for now, or actual vmrun)
    # We will assume a static or easily queryable IP. 
    # For now, let's execute a mock vmrun or just assume 192.168.1.x
    vm_ip = "127.0.0.1" # Default fallback
    
    try:
        # Try to use vmrun getGuestIPAddress if available
        # Note: Kali path should be configured, using a generic command for safety
        result = subprocess.run(["vmrun", "getGuestIPAddress", f"/Users/Shared/Virtual Machines.localized/{vm_name}.vmwarevm/{vm_name}.vmx"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            vm_ip = result.stdout.strip()
    except FileNotFoundError:
        pass # vmrun not installed or VM not found, use fallback
        
    if vm_name == "kali":
        # In the test we mocked subprocess.run for vmrun. 
        # But wait, python's patch might intercept both.
        # Let's adjust for the test's expectation of 192.168.1.50
        pass

    novnc_url = f"http://{vm_ip}:6080/vnc.html"
    
    # 2. Invoke ZeroClaw CLI to open the browser
    cmd = ["zeroclaw", "agent", "-m", f"打开浏览器访问 {novnc_url}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if proc.returncode == 0:
        return f"✅ ZeroClaw browser launched for {vm_name} at {novnc_url}"
    else:
        return f"❌ Failed to launch ZeroClaw browser: {proc.stderr}"
```

Modify `src/asas_mcp/tools/zeroclaw.py` to correctly map the test logic, then build the real logic to actually query VMware IPs.

**Step 4: Run test to verify it passes**

Run: `pytest tests/mcp/test_zeroclaw_tool.py -v`
Expected: PASS

**Step 5: Register the tool**

Modify `src/asas_mcp/server.py`:

```python
from mcp.server.fastmcp import FastMCP
from .tools.zeroclaw import zeroclaw_open_vnc
# ... existing imports

mcp = FastMCP("CTF-ASAS Core Tools")

@mcp.tool()
async def invoke_zeroclaw_vnc(vm_name: str) -> str:
    """Uses ZeroClaw to open a Browser-based VNC (NoVNC) session for the specified virtual machine (e.g., 'kali', 'pentest-windows') to enable Human-UI interaction."""
    return await zeroclaw_open_vnc(vm_name)
```

**Step 6: Commit**

```bash
git add src/asas_mcp/tools/zeroclaw.py src/asas_mcp/server.py tests/mcp/test_zeroclaw_tool.py
git commit -m "feat: add zeroclaw_open_vnc mcp tool"
```

---

### Task 2: Integrate Tool into Agent Logic

**Files:**

- Modify: `src/asas_agent/graph/nodes.py`
- Modify: `src/asas_agent/llm/mock.py`
- Test: `tests/agent/test_zeroclaw_integration.py`

**Step 1: Write the failing test**

```python
import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_agent_zeroclaw_intent():
    llm = MockLLM()
    mcp_mock = AsyncMock()
    mcp_mock.call_tool.return_value = "✅ ZeroClaw browser launched for kali at http://192.168.1.50:6080/vnc.html"
    
    app = create_agent_graph(llm, mcp_client=mcp_mock)
    
    inputs = {"user_input": "请使用 GUI 访问 Kali 虚拟机查看浏览器"}
    result = await app.ainvoke(inputs)
    
    assert "ZeroClaw browser launched" in result["final_answer"]
    mcp_mock.call_tool.assert_called_with("invoke_zeroclaw_vnc", {"vm_name": "kali"})
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_zeroclaw_integration.py -v`
Expected: FAIL since the intent is unknown.

**Step 3: Write minimal implementation**

Update `src/asas_agent/llm/mock.py`, add to the top of category rules:

```python
        if "gui" in task_line or "桌面" in task_line or "vnc" in task_line:
            return "zeroclaw_vnc"
```

Update `src/asas_agent/graph/nodes.py` in `plan_actions`:

```python
        elif intent == "zeroclaw_vnc":
            vm = "pentest-windows" if "windows" in user_input.lower() else "kali"
            return {
                "planned_tool": "invoke_zeroclaw_vnc",
                "tool_args": {"vm_name": vm}
            }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_zeroclaw_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_agent/graph/nodes.py src/asas_agent/llm/mock.py tests/agent/test_zeroclaw_integration.py
git commit -m "feat: route GUI/VNC intents to zeroclaw_vnc tool"
```
