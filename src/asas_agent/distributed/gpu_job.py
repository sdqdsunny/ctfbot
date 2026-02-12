from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import time
import uuid

@dataclass
class CrackJob:
    """Represents a distributed Hashcat cracking job."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hash_value: str = ""
    hash_type: str = "0" # MD5 default
    wordlist: str = "rockyou.txt"
    priority: int = 10 # Higher is better
    
    # State tracking
    status: str = "PENDING" # PENDING, RUNNING, PAUSED, COMPLETED, FAILED
    assigned_worker_id: Optional[str] = None
    progress_percent: float = 0.0
    checkpoint_data: str = "" # Base64 encoded hashcat restore session/checkpoint
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "hash_value": self.hash_value,
            "hash_type": self.hash_type,
            "priority": self.priority,
            "status": self.status,
            "worker": self.assigned_worker_id,
            "progress": self.progress_percent,
            "result": self.result
        }
