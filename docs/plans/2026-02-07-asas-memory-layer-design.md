# ASAS Memory Layer (RAG) Design

## 1. Overview

The Memory Layer is a dedicated MCP Server (`asas-memory-mcp`) designed to provide **Retrieval-Augmented Generation (RAG)** capabilities to the ASAS Agent.
It enables the agent to access a local, persistent knowledge base of CTF writeups, payloads, and tool usage guides, which is critical for **offline/local LLM scenarios** where the model's internal knowledge may be limited.

## 2. Architecture

### 2.1 Component Diagram

```mermaid
graph TD
    Agent[ASAS Agent] -->|MCP Protocol (Stdio)| MemoryServer[ASAS Memory MCP]
    MemoryServer -->|Embed & Query| ChromaDB[(ChromaDB Local)]
    
    subgraph Data Persistence
        ChromaDB -->|Writes| Disk[./data/chroma_db/]
        Loader[Initial Loader] -->|Reads| KB[./data/knowledge_base/*.md]
        Loader -->|Upserts| ChromaDB
    end
```

### 2.2 Technology Stack

- **Language**: Python 3.10+ (Recommended: 3.11/3.12 for ONNX compatibility)
- **Database**: **ChromaDB** (Embedded mode)
- **Embedding Model**: `all-MiniLM-L6-v2` (via `sentence-transformers` / `chromadb.utils.embedding_functions`)
- **Protocol**: MCP (Model Context Protocol) via `mcp` SDK (FastMCP)

## 3. Data Structure

### 3.1 Knowledge Schema (ChromaDB Collection)

- **Collection Name**: `ctf_knowledge`
- **Fields**:
  - `id`: (String) Unique UUID or filename based hash.
  - `document`: (String) The actual text chunk.
  - `metadata`: (Dict)
    - `title`: (String) Title of the knowledge snippet.
    - `category`: (String) `web`, `pwn`, `crypto`, `misc`, `reverse`, `mobile`.
    - `source`: (String) filename or "user_added".
    - `timestamp`: (Float) Creation time.

### 3.2 Directory Structure

```text
ctfbot/
├── data/
│   ├── chroma_db/          # Persistent storage for ChromaDB
│   └── knowledge_base/     # Initial markdown files
│       ├── web_sqli.md
│       ├── linux_privesc.md
│       └── crypto_classical.md
├── src/
│   ├── asas_memory/
│   │   ├── __init__.py
│   │   ├── server.py       # MCP Entrypoint
│   │   ├── db.py           # Database wrapper (Singleton)
│   │   └── loader.py       # Boot-time file loader
│   └── ...
```

## 4. MCP Tools Interface

### 4.1 `memory_query`

Search the knowledge base for relevant information.

- **Input**:
  - `query` (string, required): The search text (e.g., "sql injection payload for login").
  - `n_results` (integer, optional): Number of results to return (default: 3).
  - `category` (string, optional): Filter by category (`web`, `pwn`, etc.).

- **Output**:
  - Markdown formatted string containing the top matching documents with their titles and sources.

### 4.2 `memory_add`

Add new knowledge to the database.

- **Input**:
  - `content` (string, required): The information to store.
  - `title` (string, required): A short descriptive title.
  - `category` (string, required): One of `web`, `pwn`, `crypto`, `misc`, `reverse`, `mobile`.

- **Output**:
  - Confirmation message with the generated ID.

## 5. Development Plan

### Phase 1: Core Implementation

1. **Project Setup**: Add `chromadb` dependency, define file structure.
2. **Database Logic**: Implement `ChromaManager` class for handling collections and embeddings.
3. **MCP Server**: Implement `asas-memory-mcp` with `fastmcp`.
4. **Initial Knowledge**: Create dummy markdown files for testing.

### Phase 2: Integration

1. **Client Update**: Update `asas-agent` to support connecting to `asas-memory-mcp` (or both MCP servers).
    - *Note: For MVP, we might run memory server as a separate tool or merge into core if managing multiple servers is complex in current Agent client. Decision: Keep separate, Agent Client needs to support multiple servers or we merge capabilities?*
    - *Refinement*: To keep it simple for MVP, we can run `asas-memory-mcp` as a separate process, but the current `MCPToolClient` in Agent is hardcoded to `asas_mcp`. We need to generalize `MCPToolClient` to support selecting which server to call, or (simpler for now) **merge the Memory tools into `asas-core-mcp` module** to avoid managing multiple subprocesses in the MVP Agent.

    *Decision Update*: **Integrated Approach**. instead of a separate process `asas-memory-mcp`, we will implement the memory module *inside* `asas_mcp` server as a new capability. This simplifies deployment (single MCP server process) and configuration for the CLI agent. The logical separation remains in `src/asas_mcp/memory/`.

## 6. Revised Implementation Strategy (Integrated)

To avoid the complexity of Orchestrating multiple MCP servers in the python client for this MVP phase, we will add the Memory capability to the existing `asas-core-mcp` server.

- **New Path**: `src/asas_mcp/tools/memory.py`
- **New Data Path**: `ctfbot/data/...`
- **Dependencies**: Add `chromadb` to main `pyproject.toml`.

This ensures the `asas_agent` can immediately use memory tools without changing its client architecture.
