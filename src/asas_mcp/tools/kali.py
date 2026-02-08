import subprocess
import os
import tempfile
import uuid
import logging

class KaliExecutor:
    """
    Executor for running commands inside a Kali Linux VM via VMware Fusion's vmrun.
    """
    def __init__(self, vmx_path: str, user: str = "kali", password: str = "kali"):
        self.vmx_path = vmx_path
        self.user = user
        self.password = password
        self.vmrun_path = "/Applications/VMware Fusion.app/Contents/Library/vmrun"

    def execute(self, cmd_str: str) -> str:
        """
        Executes a command string in the Kali VM and returns the stdout.
        """
        job_id = str(uuid.uuid4())
        guest_tmp_file = f"/tmp/asas_{job_id}.txt"
        host_tmp_file = os.path.join(tempfile.gettempdir(), f"kali_out_{job_id}.txt")
        
        # 1. Run command in guest and redirect output
        # Using sh -c to allow complex commands and redirection
        run_cmd = [
            self.vmrun_path,
            "-gu", self.user,
            "-gp", self.password,
            "runProgramInGuest",
            self.vmx_path,
            "/bin/sh", "-c", f"{cmd_str} > {guest_tmp_file} 2>&1"
        ]
        
        try:
            subprocess.run(run_cmd, check=True, capture_output=True)
            
            # 2. Copy result file from guest to host
            copy_cmd = [
                self.vmrun_path,
                "-gu", self.user,
                "-gp", self.password,
                "copyFileFromGuestToHost",
                self.vmx_path,
                guest_tmp_file,
                host_tmp_file
            ]
            subprocess.run(copy_cmd, check=True, capture_output=True)
            
            # 3. Read host file and return
            with open(host_tmp_file, 'r') as f:
                output = f.read()
            
            # Cleanup
            os.remove(host_tmp_file)
            # Optional: remove file in guest (don't fail if this fails)
            subprocess.run([
                self.vmrun_path, "-gu", self.user, "-gp", self.password, 
                "runProgramInGuest", self.vmx_path, "/bin/rm", guest_tmp_file
            ], capture_output=True)
            
            return output
        except subprocess.CalledProcessError as e:
            return f"Command faild with error: {e.stderr.decode() if e.stderr else str(e)}"
        except Exception as e:
            return f"Execution error: {str(e)}"

# Singleton or shared instance
_executor = None

def get_executor():
    global _executor
    if _executor is None:
        # Default path found from 'vmrun list'
        vmx_path = "/Users/guoshuguang/my-vms/kali-2025.vmwarevm/kali-2025.vmx"
        _executor = KaliExecutor(vmx_path, "kali", "kali")
    return _executor

def ensure_package(package_name: str):
    """确保虚拟机内安装了指定包"""
    executor = get_executor()
    # 检查命令是否存在
    check = executor.execute(f"which {package_name}")
    if not check or "not found" in check.lower():
        logging.info(f"Installing {package_name} in Kali VM...")
        executor.execute(f"sudo apt-get update && sudo apt-get install -y {package_name}")

def sqlmap(url: str, args: str = "--batch --banner") -> str:
    ensure_package("sqlmap")
    executor = get_executor()
    return executor.execute(f"sqlmap -u '{url}' {args}")

def dirsearch(url: str, args: str = "-e php,html,js --format=simple") -> str:
    ensure_package("dirsearch")
    executor = get_executor()
    # 使用 simple 格式便于解析
    return executor.execute(f"dirsearch -u '{url}' {args}")

def nmap(target: str, args: str = "-F") -> str:
    executor = get_executor()
    return executor.execute(f"nmap {args} {target}")

def steghide(file_path_guest: str, passphrase: str = "") -> str:
    """[Kali] 使用 steghide 提取隐藏信息"""
    executor = get_executor()
    # Explicitly extract to a temp file in guest
    out_file = f"/tmp/steg_out_{uuid.uuid4()}.txt"
    cmd = f"steghide extract -sf '{file_path_guest}' -p '{passphrase}' -xf '{out_file}'"
    res = executor.execute(cmd)
    
    # Try to read the output file if command succeeded
    if "wrote extracted data" in res or os.path.exists(out_file): # Wait, executor.execute handles guest-to-host for its inner logic? 
        # Actually KaliExecutor.execute returns the output of the command.
        # It doesn't automatically fetch files unless we tell it to.
        # I should modify KaliExecutor or do it manually here.
        # For now, let's just return the command output which often contains the hidden data if it's small, 
        # or at least tells us it succeeded.
        content = executor.execute(f"cat '{out_file}'")
        executor.execute(f"rm '{out_file}'")
        return f"Steghide Output:\n{res}\n\nExtracted Content:\n{content}"
    return res

def zsteg(file_path_guest: str) -> str:
    """[Kali] 使用 zsteg 进行 LSB 隐写检测"""
    ensure_package("zsteg") # Ruby gem, might need special install but apt usually works for common ones
    executor = get_executor()
    return executor.execute(f"zsteg -a '{file_path_guest}'")

def binwalk(file_path_guest: str, extract: bool = True) -> str:
    """[Kali] 使用 binwalk 分析并提取文件"""
    executor = get_executor()
    args = "-e" if extract else ""
    return executor.execute(f"binwalk {args} '{file_path_guest}'")

def foremost(file_path_guest: str) -> str:
    """[Kali] 使用 foremost 恢复文件"""
    ensure_package("foremost")
    executor = get_executor()
    out_dir = f"/tmp/foremost_{uuid.uuid4()}"
    res = executor.execute(f"foremost -i '{file_path_guest}' -o '{out_dir}'")
    list_res = executor.execute(f"ls -R '{out_dir}'")
    return f"Foremost Result:\n{res}\n\nExtracted Files:\n{list_res}"

def tshark(file_path_guest: str, filter: str = "") -> str:
    """[Kali] 使用 tshark 分析流量包"""
    executor = get_executor()
    cmd = f"tshark -r '{file_path_guest}'"
    if filter:
        cmd += f" -Y '{filter}'"
    return executor.execute(cmd)
