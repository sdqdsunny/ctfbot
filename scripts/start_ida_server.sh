#!/bin/bash
# Helper script to launch headless IDA Pro MCP server

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_binary>"
    exit 1
fi

BINARY_PATH=$1

echo "🚀 Starting idalib-mcp server for: $BINARY_PATH"
# Use uv to run the idalib-mcp component from the project
# Note: Requires idalib to be installed and licensed on the host
uv run idalib-mcp --host 127.0.0.1 --port 8745 "$BINARY_PATH"
