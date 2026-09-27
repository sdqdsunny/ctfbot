from langchain_core.tools import tool
import os
from ..executors.docker_manager import get_docker_manager
import time
import json

@tool
async def pwn_fuzz_start(binary_path: str, duration_sec: int = 600) -> str:
    """
    针对指定的二进制文件启动一个 AFL++ (QEMU 模式) Fuzzer。
    会创建一个隔离的 Docker 容器并在后台运行。
    
    Args:
        binary_path: 需要 Fuzz 的二进制文件在本地的路径。
        duration_sec: Fuzzing 运行的时长（单位秒），默认 10 分钟。
        
    Returns:
        包含 Container ID 的成功信息或错误信息。
    """
    dm = get_docker_manager()
    binary_name = os.path.basename(binary_path)
    
    # 1. 尝试启动容器
    container = dm.start_fuzzer_container(binary_path)
    if not container:
        return "Failed to start fuzzer container. Check docker daemon."
    
    # 2. 准备初始化文件夹
    dm.exec_command(container.id, "mkdir -p /data/in /data/out")
    dm.exec_command(container.id, "echo 'hello' > /data/in/seed")
    
    # 3. 启动 AFL++ (后台异步运行)
    # 使用 afl-fuzz -Q (QEMU 模式) -i (输入) -o (输出) -- /data/binary
    fuzz_cmd = f"timeout {duration_sec} afl-fuzz -Q -i /data/in -o /data/out -- /data/{binary_name}"
    
    # 我们使用 nohup 或类似方式在容器后台执行，或者让容器主进程保持运行并在 exec 中触发
    # 这里通过 exec_run 的 detach 参数（如果底层支持）或 shell 后台运行
    dm.exec_command(container.id, f"bash -c 'nohup {fuzz_cmd} > /data/fuzz.log 2>&1 &'")
    
    return json.dumps({
        "status": "started",
        "container_id": container.id,
        "binary": binary_name,
        "output_dir": "/data/out",
        "message": f"Fuzzing session started for {duration_sec}s. Use pwn_fuzz_check to monitor."
    })

@tool
async def pwn_fuzz_check(container_id: str) -> str:
    """
    检查 Fuzzing 任务的实时遥测数据（Coverage 和 Crashes）。
    
    Args:
        container_id: Fuzzer 容器的 ID。
    """
    import re
    dm = get_docker_manager()
    raw_stats = dm.exec_command(container_id, "afl-whatsup /data/out")
    
    # 简单的正则解析
    data = {
        "raw": raw_stats,
        "fuzzers": [],
        "total_paths": 0,
        "unique_crashes": 0,
        "execs_per_sec": 0
    }
    
    # 提取总数 (afl-whatsup 汇总行)
    # 例子: total paths 30, unique crashes 0
    paths_match = re.search(r"total paths (\d+)", raw_stats)
    crashes_match = re.search(r"unique crashes (\d+)", raw_stats)
    execs_match = re.search(r"speed (\d+) execs/sec", raw_stats)
    
    if paths_match: data["total_paths"] = int(paths_match.group(1))
    if crashes_match: data["unique_crashes"] = int(crashes_match.group(1))
    if execs_match: data["execs_per_sec"] = int(execs_match.group(1))
    
    return json.dumps(data)

@tool
async def pwn_fuzz_triage(container_id: str, crash_filename: str) -> str:
    """
    自动分析 Fuzzer 发现的崩溃文件。
    使用 GDB-Exploitable 插件进行画像。
    
    Args:
        container_id: Fuzzer 容器的 ID。
        crash_filename: 崩溃文件的名称（在 /data/out/default/crashes/ 下）。
    """
    dm = get_docker_manager()
    
    # 找到二进制文件名（通过 ls /data）
    target_files = dm.exec_command(container_id, "ls /data").split()
    # 简单启发式排除目录
    binaries = [f for f in target_files if f not in ['in', 'out', 'fuzz.log', 'seed']]
    if not binaries:
        return "Error: Could not identify target binary in /data"
    binary_name = binaries[0]

    # 构建 GDB 指令进行 triage
    # gdb -batch -ex "run < /path/to/crash" -ex "exploitable" /path/to/binary
    crash_path = f"/data/out/default/crashes/{crash_filename}"
    triage_cmd = f"gdb -batch -ex 'run < {crash_path}' -ex 'exploitable' /data/{binary_name}"
    
    report = dm.exec_command(container_id, triage_cmd)
    
    return f"--- Crash Triage Report for {crash_filename} ---\n{report}"
