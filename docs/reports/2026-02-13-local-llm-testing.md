# Local LLM Testing & Orchestrator Hardening Report (2026-02-13)

## 1. Overview

This session focused on testing the ASAS Agent v3 with local LLMs (DeepSeek-R1-Distill-Llama-8B and GPT-OSS-20B) via LM Studio. The primary task was to script a brute-force attack on DVWA (`http://10.255.1.2:81/login.php`) using `kali_exec`.

## 2. Key Changes & Improvements

### Core Logic (`src/asas_agent/graph/workflow.py`)

- **Robust Tool Parsing**:
  - Enhanced `_parse_manual_tool_calls` regex to correctly handle complex, multiline `cmd_str` arguments, dealing with nested quotes and Python code blocks.
  - Added logic to strip `<thought>...</thought>` tags, supporting reasoning models like DeepSeek R1.
- **Prompt Engineering**:
  - Updated Orchestrator system prompt to enforce a **"Write-then-Run"** workflow (using `cat <<EOF` followed by `python3`).
  - Added specific guidance and a code template for handling DVWA's rolling CSRF tokens.

### Infrastructure

- **CLI (`src/asas_agent/__main__.py`)**: Added `lmstudio` as a supported LLM provider option.
- **LLM Factory (`src/asas_agent/llm/factory.py`)**: Increased timeout for LM Studio requests to 600s to accommodate slower local inference.
- **Config**: Created `v3_local.yaml` for local testing.

## 3. Findings & Limitations

- **Tool Parsing**: The regex improvements were successful. The system can now correctly parse long Python scripts embedded in tool arguments, provided the LLM generates them completely.
- **Local LLM Performance**:
  - **8B Model**: Struggled with complex instruction following (skipping the "write" step) and suffered from output truncation when generating full scripts.
  - **20B Model**: Better instruction following (attempted to use `cat`), but still faced output truncation issues with long tool arguments, preventing successful script execution.
- **Decision**: The user decided to revert to larger, online/commercial LLMs (e.g., DeepSeek V3, GPT-4) for future functional testing to ensure reliability and avoid "fighting the model."

## 4. Next Steps (Planned for Next Session)

1. **Switch Context**: Revert config to use online models (e.g., `v3_deepseek.yaml` or `v3_config.yaml` pointing to a robust provider).
2. **Resume Task**:
    - Target: `http://10.255.1.2:81/login.php`
    - Goal: Brute-force admin password using `/tmp/passwords.txt`.
    - Method: Use `kali_exec` to write and run a Python script that handles CSRF tokens correctly.
3. **Post-Login**: Once independent login is achieved, proceed to SQL injection vulnerability scanning.

## 5. Environment State

- **Codebase**: All regex and prompt improvements in `workflow.py` are committed and saved.
- **Config**: `v3_local.yaml` exists for future local testing if needed.
- **Deps**: `lmstudio` support in CLI is preserved.
