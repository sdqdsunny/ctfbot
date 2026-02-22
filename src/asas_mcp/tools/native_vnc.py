from .vnc_core import VNCHelper
from .vms_vnc import get_vm_ip

async def _get_helper(vm_name: str, port: int = 5900, password: str = None) -> VNCHelper:
    ip = await get_vm_ip(vm_name)
    if ip.startswith("Error"):
        raise ValueError(ip)
    return VNCHelper(host=ip, port=port, password=password)

async def vnc_screenshot(vm_name: str, port: int = 5900, password: str = None) -> str:
    """Takes a screenshot of the specified VM's VNC screen."""
    try:
        helper = await _get_helper(vm_name, port, password)
        return await helper.take_screenshot()
    except Exception as e:
        return f"VNC Screenshot Error: {str(e)}"

async def vnc_mouse_click(vm_name: str, x: int, y: int, button: str = "left", port: int = 5900, password: str = None) -> str:
    """Moves the mouse to (x, y) and performs a click on the specified VM."""
    try:
        helper = await _get_helper(vm_name, port, password)
        return await helper.mouse_click(x, y, button)
    except Exception as e:
        return f"VNC Mouse Error: {str(e)}"

async def vnc_keyboard_type(vm_name: str, text: str, port: int = 5900, password: str = None) -> str:
    """Types the specified text on the specified VM."""
    try:
        helper = await _get_helper(vm_name, port, password)
        return await helper.keyboard_type(text)
    except Exception as e:
        return f"VNC Keyboard Error: {str(e)}"
