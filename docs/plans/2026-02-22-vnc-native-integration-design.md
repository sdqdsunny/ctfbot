# v7.0 VNC Native Integration Design (Option B)

**Date**: 2026-02-22
**Goal**: Integrate a native, headless VNC client protocol into the CTF-ASAS agent to enable visual tracking and GUI manipulation of target virtual machines (Kali & Windows) without hijacking the host macOS physical mouse and keyboard.

## 1. Architecture Overview (Native VNC Protocol)

Instead of using a generic, host-level UI automation tool (like PyAutoGUI) that takes over the human's physical screen, we will embed a VNC client directly within the Python agent codebase. The agent will connect to the target VM's VNC Server over the internal network (TCP 5900).

- **Agent VNC Client Layer:** A headless VNC connection manager. It pulls framebuffer updates (screenshots) and sends exact X,Y pointer events or keystrokes directly into the VNC socket.
- **Human Observer (NoVNC):** The human operator can simultaneously connect to the same target VM using the NoVNC web dashboard (port 6080) to observe the agent's visual actions in real-time, just like watching a movie.
- **MCP Tool Abstraction:** The VNC client capabilities will be exposed to the LLM (DeepSeek) as standard MCP tools (`vnc_get_screen`, `vnc_mouse_click`, `vnc_keyboard_type`).

## 2. Component Design

### 2.1 Virtual Machine Pre-requisites

Both target VMs (`kali` and `pentest-windows`) must run a VNC Server accessible on port 5900 (or customized). A NoVNC wrapper is optional but highly recommended on port 6080 for human observation. (This step has largely been completed in previous manual setups).

### 2.2 Core VNC Client (`src/asas_mcp/tools/vnc_core.py`)

We will leverage established Python libraries such as `asyncvnc` or `vncdotool` to manage the lifecycle of the VNC connection.
Responsibilities:

- Maintain an active connection or establish it on-demand based on `vm_ip`.
- Capture the current frame/screen as an image buffer.
- Map coordinates and transmit `PointerEvent` (Mouse Click/Drag).
- Transmit `KeyEvent` (Keyboard inputs).

### 2.3 Expanded MCP Tools

The agent needs precise tools to navigate GUI applications like Ghidra, browsers, or thick clients:

- `vnc_connect(vm_ip: str, port: int = 5900, password: str = None)`
- `vnc_screenshot() -> str (base64 image)`
- `vnc_mouse_move(x: int, y: int)`
- `vnc_mouse_click(x: int, y: int, button: str = "left", clicks: int = 1)`
- `vnc_keyboard_type(text: str)`
- `vnc_keyboard_press(key: str)` (e.g., 'enter', 'tab', 'ctrl+c')

### 2.4 Orchestrator LLM Configuration

The `v3` architecture prompts must be updated so the model understands:
"If a visual interface is required, use `vnc_screenshot` to view the screen, then use `vnc_mouse_click` with X,Y coordinates to interact."
Since DeepSeek supports Vision capabilities (if configured as `deepseek-vl` or if we pass the visual data through), we must ensure the `_arun` adapter supports base64 image parsing or prompt insertion for multimodal contexts. (If using standard `deepseek-chat`, we may need a lightweight local OCR/UI-parser node, but Anthropic Computer Use API handles this natively if we switch models. Design choice here depends on the chosen LLM's vision support).

## 3. Trade-offs and Considerations

- **Pros:**
  - Perfect isolation: Does not interfere with the human operator's physical workspace.
  - Highly robust: Bypasses complex zero-claw dependencies and connects straight to the source.
  - Supports continuous human observation via NoVNC without input clash.
- **Cons:**
  - The model doing the reasoning MUST support Vision (reading screenshots) to know where to click. If the currently used DeepSeek API lacks vision, we may need to bridge a Vision Model (like Claude-3.5-Sonnet or GPT-4o) specifically for the GUI-Navigation node, or use purely coordinate-based guesswork via OCR.

## 4. Implementation Steps

1. Select and install the Python VNC client library.
2. Build the `vnc_core.py` abstraction.
3. Wrap it into MCP standard tools and expose them in `server.py`.
4. Test with a simple task: "Open the desktop and click the terminal icon" using a mock or mixed-model workflow.
