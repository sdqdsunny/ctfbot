# ASAS Core MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Initialize the CTF-ASAS project, set up the Core MCP Server infrastructure, and implement the first atomic tool (`recon.scan`) with TDD to validate the architecture.

**Architecture:**

- **Language:** Python 3.10+ with Poetry for dependency management.
- **Framework:** `mcp` (Model Context Protocol) SDK for the server.
- **Testing:** `pytest` for unit/integration tests.
- **Containerization:** Docker (basic setup).
- **Structure:** Modular design separating `tools` (implementations) from the `server` (MCP interface).

**Tech Stack:** Python 3.10+, Poetry, MCP SDK, Pytest, Docker (basic setup).

---

### Task 1: Project Scaffolding & Dependency Setup

**Files:**

- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/asas_mcp/__init__.py`
- Create: `src/asas_mcp/server.py`
- Create: `tests/__init__.py`
- Create: `tests/test_version.py`

**Step 1: Initialize Poetry and Dependencies**

**pyproject.toml**

```toml
[tool.poetry]
name = "asas-core-mcp"
version = "0.1.0"
description = "Core MCP Server for CTF-ASAS"
authors = ["ASAS Team"]

[tool.poetry.dependencies]
python = "^3.10"
mcp = "^0.1.0"  # Assuming generic MCP SDK availability or placeholder
fastapi = "^0.100.0"
uvicorn = "^0.20.0"
python-nmap = "^0.7.1" # For recon tool

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^23.0.0"
isort = "^5.0.0"
mypy = "^1.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 2: Create Basic Directory Structure**

```bash
mkdir -p src/asas_mcp tests
touch src/asas_mcp/__init__.py
touch tests/__init__.py
```

**Step 3: Write the failing test for version check**

**tests/test_version.py**

```python
from asas_mcp import __version__

def test_version():
    assert __version__ == "0.1.0"
```

**Step 4: Run test to verify it fails**

Run: `pytest tests/test_version.py -v`
Expected: FAIL (ImportError or version mismatch)

**Step 5: Write minimal implementation**

**src/asas_mcp/**init**.py**

```python
__version__ = "0.1.0"
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_version.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add pyproject.toml src/asas_mcp/__init__.py tests/test_version.py
git commit -m "chore: init project structure and dependencies"
```

---

### Task 2: Basic MCP Server Skeleton

**Files:**

- Create: `src/asas_mcp/server.py`
- Create: `tests/test_server.py`

**Step 1: Write the failing test for server instantiation**

**tests/test_server.py**

```python
import pytest
from asas_mcp.server import create_app

def test_server_creation():
    app = create_app()
    assert app is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_server.py -v`
Expected: FAIL (ImportError)

**Step 3: Write minimal implementation**

**src/asas_mcp/server.py**

```python
from fastapi import FastAPI
# In a real MCP implementation, this would involve the MCP SDK's Server class.
# For now, we wrap it in a function that returns the app/server instance.

def create_app():
    app = FastAPI(title="ASAS Core MCP")
    # MCP initialization logic would go here
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_server.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_mcp/server.py tests/test_server.py
git commit -m "feat: add basic server skeleton"
```

---

### Task 3: Implement `recon.scan` Tool (Mocked)

**Files:**

- Create: `src/asas_mcp/tools/recon.py`
- Modify: `src/asas_mcp/server.py`
- Create: `tests/tools/test_recon.py`

**Step 1: Write the failing test for recon tool**

**tests/tools/test_recon.py**

```python
import pytest
from asas_mcp.tools import recon

def test_scan_basic():
    # Mocking would be used in real integration, but unit test checks function signature/return
    result = recon.scan(target="127.0.0.1", ports="80")
    assert "scan_result" in result
    assert result["target"] == "127.0.0.1"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/tools/test_recon.py -v`
Expected: FAIL (ModuleNotFoundError)

**Step 3: Write minimal implementation**

**src/asas_mcp/tools/recon.py**

```python
import subprocess
import json
from typing import Dict, Any

def scan(target: str, ports: str = "1-1000") -> Dict[str, Any]:
    """
    Executes a basic nmap scan.
    For MVP, we might mock the actual nmap call if not installed, 
    or return a structured dict simulating output.
    """
    # Simulate scan result for MVP structure validation
    return {
        "target": target,
        "ports": ports,
        "scan_result": {
            "open_ports": [80],
            "os": "Linux"
        },
        "status": "success"
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/tools/test_recon.py -v`
Expected: PASS

**Step 5: Register tool in Server (Integration)**

**tests/test_server_integration.py**

```python
# Verify tool is registered
# Depending on MCP SDK, we would check server.list_tools()
pass
```

**Step 6: Commit**

```bash
git add src/asas_mcp/tools/recon.py tests/tools/test_recon.py
git commit -m "feat: implement basic recon.scan tool"
```

---

### Task 4: Crypto Tool - Base64 Decoder

**Files:**

- Create: `src/asas_mcp/tools/crypto.py`
- Create: `tests/tools/test_crypto.py`

**Step 1: Write the failing test**

**tests/tools/test_crypto.py**

```python
from asas_mcp.tools import crypto

def test_decode_base64():
    encoded = "SGVsbG8gV29ybGQ="
    decoded = crypto.decode(encoded, method="base64")
    assert decoded == "Hello World"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/tools/test_crypto.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

**src/asas_mcp/tools/crypto.py**

```python
import base64

def decode(content: str, method: str = "auto") -> str:
    if method == "base64":
        return base64.b64decode(content).decode('utf-8')
    # Add auto-detection logic later
    return content
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/tools/test_crypto.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_mcp/tools/crypto.py tests/tools/test_crypto.py
git commit -m "feat: implement crypto.decode tool"
```
