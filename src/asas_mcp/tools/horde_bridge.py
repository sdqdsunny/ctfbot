from langchain_core.tools import tool
import json
import base64
from ..executors.docker_manager import get_docker_manager

@tool
async def pwn_horde_get_seeds(container_id: str) -> str:
    """
    从 Fuzzer 容器中提取当前发现的所有有趣种子（Corpus）。
    返回种子文件列表及其内容的十六进制表示。
    """
    dm = get_docker_manager()
    queue_dir = "/data/out/default/queue/"
    files = dm.list_files(container_id, queue_dir)
    
    seeds = {}
    # 只取前 10 个最有代表性的（简单的启发式：取最后发现的几个）
    # 在 AFL++ 中，通常 id 越大越深
    for filename in sorted(files, reverse=True)[:10]:
        content = dm.read_file(container_id, f"{queue_dir}{filename}")
        if content:
            seeds[filename] = content.hex()
            
    return json.dumps({
        "container_id": container_id,
        "seeds_count": len(seeds),
        "seeds": seeds
    })

@tool
async def pwn_horde_inject_seed(container_id: str, seed_hex: str, filename: str = "angr_solve") -> str:
    """
    将解算出的结果作为新种子注入 Fuzzer 的输入队列。
    这能帮助 Fuzzer 跨越原本无法绕过的逻辑门。
    """
    dm = get_docker_manager()
    content = bytes.fromhex(seed_hex)
    # 注入到 in 目录，AFL++ 会在下一次循环或作为新种子扫描到
    # 实际上如果是运行中的 AFL++，最好注入到 queue 目录，但 AFL++ 可能会报错（校验不通过）
    # AFL++ 支持动态添加 seed，但最简单的是放在 in/ 重新启动，或使用 afl-fuzz 的共享模式
    # 这里我们写入 /data/in/ 作为一个新种子
    path = f"/data/in/{filename}"
    dm.write_file(container_id, path, content)
    
    return f"Success: Seed injected to {path} in container {container_id}."
