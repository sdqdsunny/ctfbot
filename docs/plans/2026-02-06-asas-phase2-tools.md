# ASAS Core MCP - Phase 2: Tool Expansion

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 扩展 Crypto、Reverse、Misc 工具集，为五大题型提供基础能力覆盖。

**Architecture:**

- 延续 Phase 1 的模块化设计
- 每个工具独立测试，遵循 TDD
- 为后续 MCP 协议集成做准备

**Tech Stack:** Python 3.10+, Pytest, 专用库（pycryptodome, angr-stub 等）

---

### Task 5: 扩展 Crypto 工具 - 多编码支持

**Files:**

- Modify: `src/asas_mcp/tools/crypto.py`
- Modify: `tests/tools/test_crypto.py`

**Step 1: 编写 Hex 解码测试**

**tests/tools/test_crypto.py** (追加)

```python
def test_decode_hex():
    encoded = "48656c6c6f20576f726c64"
    decoded = crypto.decode(encoded, method="hex")
    assert decoded == "Hello World"
```

**Step 2: 运行测试验证失败**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_crypto.py::test_decode_hex -v`
Expected: FAIL

**Step 3: 实现 Hex 解码**

**src/asas_mcp/tools/crypto.py** (修改 decode 函数)

```python
import base64
import binascii

def decode(content: str, method: str = "auto") -> str:
    """解码常见编码格式"""
    if method == "base64":
        return base64.b64decode(content).decode('utf-8')
    elif method == "hex":
        return bytes.fromhex(content).decode('utf-8')
    # Add auto-detection logic later
    return content
```

**Step 4: 运行测试验证通过**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_crypto.py -v`
Expected: PASS (2 tests)

**Step 5: 提交**

```bash
git add src/asas_mcp/tools/crypto.py tests/tools/test_crypto.py
git commit -m "feat: crypto 工具支持 Hex 解码"
git push origin main
```

---

### Task 6: Crypto 工具 - URL 编码支持

**Files:**

- Modify: `src/asas_mcp/tools/crypto.py`
- Modify: `tests/tools/test_crypto.py`

**Step 1: 编写 URL 解码测试**

**tests/tools/test_crypto.py** (追加)

```python
def test_decode_url():
    encoded = "Hello%20World%21"
    decoded = crypto.decode(encoded, method="url")
    assert decoded == "Hello World!"
```

**Step 2: 运行测试验证失败**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_crypto.py::test_decode_url -v`
Expected: FAIL

**Step 3: 实现 URL 解码**

**src/asas_mcp/tools/crypto.py** (修改)

```python
import base64
import binascii
from urllib.parse import unquote

def decode(content: str, method: str = "auto") -> str:
    """解码常见编码格式"""
    if method == "base64":
        return base64.b64decode(content).decode('utf-8')
    elif method == "hex":
        return bytes.fromhex(content).decode('utf-8')
    elif method == "url":
        return unquote(content)
    return content
```

**Step 4: 运行测试验证通过**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_crypto.py -v`
Expected: PASS (3 tests)

**Step 5: 提交**

```bash
git add src/asas_mcp/tools/crypto.py tests/tools/test_crypto.py
git commit -m "feat: crypto 工具支持 URL 解码"
git push origin main
```

---

### Task 7: Misc 工具 - 文件类型识别

**Files:**

- Create: `src/asas_mcp/tools/misc.py`
- Create: `tests/tools/test_misc.py`

**Step 1: 编写文件类型识别测试**

**tests/tools/test_misc.py**

```python
from asas_mcp.tools import misc

def test_identify_file_type():
    # PNG magic bytes
    png_header = b'\x89PNG\r\n\x1a\n'
    result = misc.identify_file_type(png_header)
    assert result["type"] == "PNG"
    assert result["mime"] == "image/png"
```

**Step 2: 运行测试验证失败**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_misc.py -v`
Expected: FAIL

**Step 3: 实现文件类型识别**

**src/asas_mcp/tools/misc.py**

```python
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
```

**Step 4: 运行测试验证通过**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_misc.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/asas_mcp/tools/misc.py tests/tools/test_misc.py
git commit -m "feat: 实现 misc 文件类型识别工具"
git push origin main
```

---

### Task 8: Reverse 工具 - 字符串提取

**Files:**

- Create: `src/asas_mcp/tools/reverse.py`
- Create: `tests/tools/test_reverse.py`

**Step 1: 编写字符串提取测试**

**tests/tools/test_reverse.py**

```python
from asas_mcp.tools import reverse

def test_extract_strings():
    # 模拟二进制数据
    binary_data = b'Hello\x00\x00World\x00Test\x00'
    result = reverse.extract_strings(binary_data, min_length=4)
    assert "Hello" in result
    assert "World" in result
    assert "Test" in result
```

**Step 2: 运行测试验证失败**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_reverse.py -v`
Expected: FAIL

**Step 3: 实现字符串提取**

**src/asas_mcp/tools/reverse.py**

```python
import re
from typing import List

def extract_strings(data: bytes, min_length: int = 4) -> List[str]:
    """从二进制数据中提取可打印字符串"""
    # 匹配连续的可打印 ASCII 字符
    pattern = rb'[\x20-\x7e]{' + str(min_length).encode() + rb',}'
    matches = re.findall(pattern, data)
    return [m.decode('ascii') for m in matches]
```

**Step 4: 运行测试验证通过**

Run: `source .venv/bin/activate && PYTHONPATH=src pytest tests/tools/test_reverse.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/asas_mcp/tools/reverse.py tests/tools/test_reverse.py
git commit -m "feat: 实现 reverse 字符串提取工具"
git push origin main
```
