import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ui_server")

from asas_agent.config_manager import config_manager

app = FastAPI(title="CTF-ASAS UI Bridge")

# 启用 CORS 以支持 Tauri 开发环境
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/config")
async def get_config():
    # 返回脱敏后的配置（不返回 Base64 原始值，仅返回是否有 Key）
    safe_config = {}
    for p_id, p_data in config_manager.providers.items():
        safe_config[p_id] = {
            "model": p_data.get("model"),
            "hasKey": bool(p_data.get("apiKey"))
        }
    return safe_config

@app.post("/config/{provider_id}")
async def update_config(provider_id: str, data: dict):
    success = config_manager.update_provider(provider_id, data)
    return {"status": "success" if success else "failed"}

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

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def receive_chat(payload: ChatMessage):
    # TODO: In future, this will interrupt/feed the Agent's reasoning loop.
    # For now, echo it back as a system message to verify UI integration.
    await manager.broadcast({
        "type": "system_message",
        "data": {
            "content": f"User instruction received: {payload.message}",
            "level": "info"
        }
    })
    return {"status": "success"}

class ApprovalResponse(BaseModel):
    action_id: str
    approved: bool
    feedback: str = ""

@app.post("/api/approve")
async def receive_approval(payload: ApprovalResponse):
    # TODO: In future, this will resume the Agent's LangGraph node execution.
    # For now, echo it back to verify the UI interaction.
    decision = "APPROVED" if payload.approved else "REJECTED"
    await manager.broadcast({
        "type": "system_message",
        "data": {
            "content": f"Action {payload.action_id} {decision}. Feedback: {payload.feedback}",
            "level": "warning" if not payload.approved else "success"
        }
    })
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from client: {data}")
            # 处理来自前端的消息（如启动任务）
            msg_json = json.loads(data)
            await manager.broadcast({
                "type": "ack",
                "message": f"Server received: {msg_json.get('type')}"
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

def run_server(port: int = 8010):
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_server()
