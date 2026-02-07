# ASAS Memory Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide the ASAS Agent with a local, persistent knowledge base (RAG) by integrating ChromaDB into the `asas-core-mcp` server.

**Architecture:** Extend existing `asas-core-mcp` with a new `memory` module. Implement a `ChromaManager` singleton for database access. Expose `memory_query` and `memory_add` tools via MCP. Pre-load initial knowledge from markdown files.

**Tech Stack:** Python 3.10+, ChromaDB, Sentence-Transformers, FastMCP.

---

### Task 1: Dependencies & Project Structure

**Files:**

- Modify: `pyproject.toml`
- Create: `src/asas_mcp/memory/__init__.py`
- Create: `data/knowledge_base/web_sqli.md`
- Create: `data/knowledge_base/linux_privesc.md`
- Create: `data/knowledge_base/crypto_classical.md`
- Test: `tests/memory/test_dependencies.py`

**Step 1: Update dependencies**

Add `chromadb` to `pyproject.toml`.

**Step 2: Create directories and dummy data**

Create `src/asas_mcp/memory/`, `data/chroma_db/` (gitkeep), and initial knowledge markdown files.

**Step 3: Write verification test**

Create a test `tests/memory/test_dependencies.py` to verify `chromadb` can be imported and initialized (in-memory mode for test).

**Step 4: Install & Verify**

Run `pip install` and run the test.

**Step 5: Commit**

```bash
git add pyproject.toml src/asas_mcp/memory data/
git commit -m "chore: setup memory layer dependencies and structure"
```

---

### Task 2: ChromaDB Manager Implementation

**Files:**

- Create: `src/asas_mcp/memory/db.py`
- Test: `tests/memory/test_db.py`

**Step 1: Write failing test**

Create `tests/memory/test_db.py` to test `ChromaManager` singleton:

- Test initialization (persistent path).
- Test `add_document` method.
- Test `query_documents` method.

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_db.py -v`
Expected: Fail (ModuleNotFoundError)

**Step 3: Implement ChromaManager**

Implement `src/asas_mcp/memory/db.py`:

- Class `ChromaManager`.
- Use `chromadb.PersistentClient`.
- Use `sentence-transformers/all-MiniLM-L6-v2` embedding function.
- Implement `add(content, metadata, id)` and `query(text, n_results, where)`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_mcp/memory/db.py tests/memory/test_db.py
git commit -m "feat: implement ChromaDB manager"
```

---

### Task 3: Knowledge Loader

**Files:**

- Create: `src/asas_mcp/memory/loader.py`
- Test: `tests/memory/test_loader.py`

**Step 1: Write failing test**

Test `load_knowledge_base`:

- Mock `os.walk` or create temp files.
- Mock `ChromaManager`.
- Verify it parses markdown files and calls `add_document`.

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_loader.py -v`
Expected: Fail

**Step 3: Implement Loader**

Implement `src/asas_mcp/memory/loader.py`:

- Function `load_initial_knowledge(db_manager)`.
- Scan `data/knowledge_base/*.md`.
- Read content, check if already exists (by hash ID), add to DB.

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_loader.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_mcp/memory/loader.py tests/memory/test_loader.py
git commit -m "feat: implement knowledge base loader"
```

---

### Task 4: MCP Tools Integration

**Files:**

- Modify: `src/asas_mcp/server.py`
- Test: `tests/test_mcp_memory_integration.py`

**Step 1: Write failing integration test**

Create `tests/test_mcp_memory_integration.py`:

- Test calling `memory_query` tool via `mcp_server`.
- Test calling `memory_add` tool via `mcp_server`.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mcp_memory_integration.py -v`

**Step 3: Implement Tools in Server**

Modify `src/asas_mcp/server.py`:

- Import `ChromaManager` and `load_initial_knowledge`.
- Initialize DB on startup (or lazy load).
- Register `@mcp.tool()` for `memory_query`.
- Register `@mcp.tool()` for `memory_add`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mcp_memory_integration.py -v`

**Step 5: Commit**

```bash
git add src/asas_mcp/server.py tests/test_mcp_memory_integration.py
git commit -m "feat: expose memory tools via MCP"
```

---

### Task 5: Agent Verification (End-to-End)

**Files:**

- Test: `tests/agent/test_memory_e2e.py`

**Step 1: Write E2E test**

Create a test using `asas_agent`'s `MCPToolClient`:

- Start the server (which includes memory).
- Call `memory_add` via client.
- Call `memory_query` via client and verify result.

**Step 2: Run test**

Run: `pytest tests/agent/test_memory_e2e.py -v`

**Step 3: Commit**

```bash
git add tests/agent/test_memory_e2e.py
git commit -m "test: add E2E verification for memory layer"
```
