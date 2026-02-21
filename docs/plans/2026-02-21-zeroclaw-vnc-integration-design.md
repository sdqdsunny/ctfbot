# v7.0 ZeroClaw VNC Integration Design

**Goal:** Integrate the open-source ZeroClaw autonomous agent runtime into CTF-ASAS to provide Browser-based VNC (NoVNC) control over VMware Fusion virtual machines (Kali & Windows). This breaks the CLI-only limitation and enables Human-in-the-Loop (HITL) GUI collaboration between the CTF player and the agent.

**Context:** The user wants to manipulate targets via GUI, allowing both the LLM agent and human to interact with the target environment simultaneously using ZeroClaw's browser capabilities.

---

## 1. Architecture Overview

We will utilize **Option A: Browser-based VNC** as the primary integration path.

- **VMware Fusion VMs (`kali` & `pentest-windows`)**: Inside the VMs, VNC Server and `novnc` will be pre-configured and exposed on specific host-accessible ports (e.g., 6080).
- **ZeroClaw MCP Tool**: ZeroClaw provides a `browser_open` / `computer_use` module. The CTF-ASAS agent will use a custom MCP tool to command ZeroClaw to open or navigate to the NoVNC URL targeting the specific VM.
- **Human-Agent Collaboration**: The ZeroClaw browser session will be visible/accessible to the human operator (CTF player). The agent can also use ZeroClaw's computer_use to read the screen or send clicks, forming a dual-control mechanism.

## 2. Component Modifications

### 2.1 Virtual Machine Preparation (Target/Attack VMs)

- Install `x11vnc` (or standard VNC Server) and `novnc` in the `kali` VM.
- Install TightVNC/RealVNC and `novnc` in the `pentest-windows` VM.
- Configure `novnc` to start on boot and bind to `0.0.0.0:6080` (or proxy via standard web server).
- Ensure host-only or NAT networking allows the macOS host to reach `http://<vm-ip>:6080/vnc.html`.

### 2.2 CTF-ASAS Agent (Orchestrator Layer)

- **MCP Client Update**: Add a new tool connection to the local ZeroClaw instance. Since ZeroClaw acts as an independent runtime with MCP capabilities, we will register dynamic tools for bridging its browser actions.
- **New Tools Registered**:
  - `zeroclaw_open_vnc(vm_name: str)`: Determines the IP of `kali` or `pentest-windows` using existing `vmrun` logic, and directs ZeroClaw to open `http://<vm-ip>:6080`.
- **LLM Reasoning**: Update `MockLLM` and the LangGraph prompts (`AgentNodes.plan_actions`) so the agent knows: "To interact with the GUI or if a visual interaction is required, use `zeroclaw_open_vnc`".

### 2.3 ZeroClaw Gateway

- Run a local ZeroClaw instance (`zeroclaw daemon`) on the macOS host.
- Configure ZeroClaw's `[browser]` capabilities to allow automation backend (`agent_browser` or `computer_use`).

## 3. Data Flow

1. **User/Prompt**: "Use Kali GUI to open BurpSuite and analyze the request."
2. **Orchestrator**: Identifies need for GUI. Calls `zeroclaw_open_vnc(vm_name="kali")`.
3. **CTF-ASAS MCP**: Sends request to ZeroClaw's MCP server endpoint.
4. **ZeroClaw**: Opens a browser pointing to `http://<kali-ip>:6080`.
5. **Human**: The browser window pops up on the host machine. The human can see Kali's GUI and take over if needed.
6. **Agent (Future/Optional)**: Can inject keystrokes/mouse clicks via ZeroClaw's `computer_use` API if required by the task.

## 4. Error Handling

- **VM Down**: If VMware `vmrun` cannot find the VM IP or the ping to port 6080 fails, the agent will report: "Kali VM or NoVNC service is offline."
- **ZeroClaw Failure**: Include fallback to CLI mode via `vmrun` if the browser fails to launch or ZeroClaw is unreachable.

## 5. Testing Plan

- **Unit Test**: Mock the ZeroClaw API response to ensure `zeroclaw_open_vnc` correctly resolves VM IPs and constructs the NoVNC URL.
- **E2E Manual Test**: Start the Kali VM, trigger the agent with a GUI task, and verify a browser automatically opens showing the Kali desktop via NoVNC, accepting both mouse input from the human and status polling from the agent.
