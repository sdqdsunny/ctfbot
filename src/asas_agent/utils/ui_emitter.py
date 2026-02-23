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
