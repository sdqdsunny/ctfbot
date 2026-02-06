from typing import Dict, Any

# 常见文件魔数
MAGIC_BYTES = {
    b'\x89PNG\r\n\x1a\n': {"type": "PNG", "mime": "image/png"},
    b'\xff\xd8\xff': {"type": "JPEG", "mime": "image/jpeg"},
    b'PK\x03\x04': {"type": "ZIP", "mime": "application/zip"},
    b'%PDF': {"type": "PDF", "mime": "application/pdf"},
}

def identify_file_type(data: bytes) -> Dict[str, Any]:
    """识别文件类型基于魔数"""
    for magic, info in MAGIC_BYTES.items():
        if data.startswith(magic):
            return info
    return {"type": "UNKNOWN", "mime": "application/octet-stream"}
