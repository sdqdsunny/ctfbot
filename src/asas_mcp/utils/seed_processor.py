import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def process_afl_seeds(seed_dir: str) -> List[bytes]:
    """
    从 AFL 队列目录读取所有原始种子。
    """
    seeds = []
    if not os.path.exists(seed_dir):
        return []
        
    for filename in os.listdir(seed_dir):
        if filename.startswith('id:'):
            path = os.path.join(seed_dir, filename)
            try:
                with open(path, 'rb') as f:
                    seeds.append(f.read())
            except Exception as e:
                logger.warning(f"Failed to read seed {filename}: {e}")
    return seeds

def select_best_seed(seeds: List[bytes]) -> bytes:
    """
    启发式选择最佳种子（目前简单选择最长的一个，因为它暗示了最深的路径）。
    """
    if not seeds:
        return b""
    return max(seeds, key=len)
