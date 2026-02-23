# Backend Connection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the Next.js frontend to the ASAS Agent backend via WebSocket to stream real-time execution logs, LLM thoughts, and tool results into the Command Center UI.

**Architecture:**
The `ui_server.py` (FastAPI) will act as a bridge. It will open a WebSocket connection to the Next.js frontend to broadcast events. It will also expose a new `POST /api/events` endpoint. The main CLI loop (`src/asas_agent/__main__.py`) will send HTTP POST requests to this endpoint during graph execution (`astream`), decoupling the UI server from the agent process. The frontend will consume the WebSocket stream to update `OrchestratorChat` and `ProcessGraph`.

**Tech Stack:** FastAPI, WebSocket, `requests`/`httpx`, React hooks, Zustand/Local State.

---

### Task 1: Setup Event Receiver & Broadcaster in UI Server

**Files:**

- Modify: `src/asas_agent/ui_server.py`
- Test: `tests/ui/test_ui_server.py` (Create)

**Step 1: Write the failing test**

```python
# Create: tests/ui/test_ui_server.py
from fastapi.testclient import TestClient
from asas_agent.ui_server import app

client = TestClient(app)

def test_emit_event_endpoint():
    # Attempt to post an event
    response = client.post("/api/events", json={
        "type": "orchestrator_message",
        "data": {"content": "Hello World"}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_ui_server.py::test_emit_event_endpoint -v`
Expected: FAIL (404 Not Found)

**Step 3: Write minimal implementation**

```python
# Add to src/asas_agent/ui_server.py
from pydantic import BaseModel

class EventPayload(BaseModel):
    type: str
    data: dict

@app.post("/api/events")
async def receive_event(payload: EventPayload):
    # Broadcast to all connected WebSockets
    await manager.broadcast({
        "type": payload.type,
        "data": payload.data
    })
    return {"status": "success"}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_ui_server.py::test_emit_event_endpoint -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_agent/ui_server.py tests/ui/test_ui_server.py
git commit -m "feat(ui): add /api/events endpoint for receiving agent execution events"
```

---

### Task 2: Create UI Emitting Utils

**Files:**

- Create: `src/asas_agent/utils/ui_emitter.py`
- Test: `tests/agent/test_ui_emitter.py` (Create)

**Step 1: Write the failing test**

```python
# Create: tests/agent/test_ui_emitter.py
import responses
from asas_agent.utils.ui_emitter import UIEmitter

@responses.activate
def test_ui_emitter():
    responses.add(
        responses.POST,
        "http://localhost:8010/api/events",
        json={"status": "success"},
        status=200
    )
    
    emitter = UIEmitter(base_url="http://localhost:8010")
    success = emitter.emit("test_event", {"foo": "bar"})
    
    assert success is True
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "http://localhost:8010/api/events"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_ui_emitter.py::test_ui_emitter -v`
Expected: FAIL (ModuleNotFoundError)

**Step 3: Write minimal implementation**

```python
# Create: src/asas_agent/utils/ui_emitter.py
import requests
import logging

logger = logging.getLogger("ui_emitter")

class UIEmitter:
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.endpoint = f"{self.base_url}/api/events"

    def emit(self, event_type: str, data: dict) -> bool:
        try:
            resp = requests.post(
                self.endpoint, 
                json={"type": event_type, "data": data},
                timeout=1.0 # Short timeout, don't block agent
            )
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Failed to emit event {event_type} to UI: {e}")
            return False

ui_emitter = UIEmitter()
```

**Step 4: Run test to verify it passes**

Run: `poetry run pip install responses` if needed
Run: `pytest tests/agent/test_ui_emitter.py::test_ui_emitter -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_agent/utils/ui_emitter.py tests/agent/test_ui_emitter.py
git commit -m "feat(agent): create UIEmitter utility to stream events to command center"
```

---

### Task 3: Instrument Main CLI with Emitting Hooks

**Files:**

- Modify: `src/asas_agent/__main__.py`

**Step 1 & 2: Bypass unit tests for entry point logic, test via integration later**

**Step 3: Write minimal implementation**

```python
# In src/asas_agent/__main__.py inside run_v3()
from asas_agent.utils.ui_emitter import ui_emitter

#... Inside async for event in app.astream(...)
        async for event in app.astream(state, config={"recursion_limit": 100}):
            if not isinstance(event, dict):
                continue
            for key, value in event.items():
                if key == "orchestrator":
                    msg = value["messages"][-1]
                    
                    # Emit orchestrator message
                    tools_used = []
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            tools_used.append({"name": tc["name"], "args": tc.get("args", {})})
                            print(f"👑 指挥官决策: 调用工具 {tc['name']}")
                            print(f"   目标/参数: {tc['args'].get('agent_type') or tc['args']}")
                    else:
                        print(f"💡 最终报告: {msg.content}")

                    ui_emitter.emit("orchestrator_message", {
                        "content": msg.content,
                        "tool_calls": tools_used
                    })

                elif key == "tools":
                    for msg in value["messages"]:
                        # Extract string summary
                        content_str = str(msg.content)[:500]
                        print(f"📥 代理返回 ({msg.name}): {content_str[:150]}...")
                        
                        ui_emitter.emit("tool_result", {
                            "tool_name": msg.name,
                            "content": content_str,
                            "is_error": "Error:" in content_str or "Failed" in content_str
                        })
```

**Step 4: Manual verification**
(Agent must be run manually, skip automated check for this specific injection step)

**Step 5: Commit**

```bash
git add src/asas_agent/__main__.py
git commit -m "feat(agent): instrument run_v3 with UI event emitter"
```

---

### Task 4: UI WebSocket Hook Integration

**Files:**

- Create: `ui/src/hooks/useAgentEvents.ts`
- Modify: `ui/src/components/OrchestratorChat.tsx`

**Step 1 & 2: UI hook manual testing**

**Step 3: Write minimal implementation**

```typescript
// Create: ui/src/hooks/useAgentEvents.ts
import { useEffect, useState } from 'react';

export interface AgentEvent {
    type: string;
    data: any;
    timestamp: number;
}

export function useAgentEvents() {
    const [events, setEvents] = useState<AgentEvent[]>([]);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8010/ws');
        
        ws.onmessage = (event) => {
            try {
                const parsed = JSON.parse(event.data);
                if (parsed.type !== 'ack') {
                    setEvents(prev => [...prev, {
                        ...parsed,
                        timestamp: Date.now()
                    }]);
                }
            } catch (e) {
                console.error("Failed to parse WS message", e);
            }
        };

        return () => ws.close();
    }, []);

    return events;
}
```

Modify `OrchestratorChat.tsx` to use the hook:

```tsx
import { useAgentEvents } from '../hooks/useAgentEvents';

// Inside component:
export default function OrchestratorChat() {
    const events = useAgentEvents();
    // ... existing state

    useEffect(() => {
        if (events.length === 0) return;
        const lastEvent = events[events.length - 1];
        
        if (lastEvent.type === 'orchestrator_message') {
            const { content, tool_calls } = lastEvent.data;
            const text = content ? content : `Executing tools: ${tool_calls.map((t:any) => t.name).join(', ')}`;
            
            setMessages(prev => [...prev, {
                id: lastEvent.timestamp.toString(),
                type: 'agent',
                content: text,
                timestamp: new Date(lastEvent.timestamp).toLocaleTimeString()
            }]);
            setIsTyping(false);
        } else if (lastEvent.type === 'tool_result') {
            const { tool_name, content, is_error } = lastEvent.data;
            setMessages(prev => [...prev, {
                id: lastEvent.timestamp.toString(),
                type: 'system',
                content: `[${tool_name}] ${is_error ? 'FAILED' : 'SUCCESS'}: ${content.substring(0, 100)}...`,
                timestamp: new Date(lastEvent.timestamp).toLocaleTimeString()
            }]);
        }
    }, [events]);
    //...
}
```

**Step 4 & 5: Commit**

```bash
git add ui/src/hooks/useAgentEvents.ts ui/src/components/OrchestratorChat.tsx
git commit -m "feat(ui): connect OrchestratorChat to live websocket events"
```
