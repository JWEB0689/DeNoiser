<div align="center">
  <h1>RTK Engine API</h1>
  <p><strong>Proprietary Token Compression & Autonomous Bypass Server</strong></p>
  <img src="https://img.shields.io/badge/Python-FastAPI-blue?style=for-the-badge" alt="Stack" />
  <img src="https://img.shields.io/badge/Access-Private-rose?style=for-the-badge" alt="Private" />
</div>

---

## Overview

The **RTK (Real-Time Knowledge) Engine** is a high-performance local Python backend built to service the [Agent Desktop](https://github.com/JWEB0689/Agent) application. 

Its primary responsibility is to intercept massive conversational payloads from the Agent client, mathematically compress the token context window using sliding-window heuristics, and proxy the optimized payload to LLM providers. This prevents token explosion in long-running autonomous sessions.

## ⚙️ How It Works

Instead of blindly sending thousands of system prompts and chat history items to an LLM, the Agent client dispatches the raw JSON to this engine. The engine applies:
1. **System Prompt Preservation:** Ensuring core directives are never dropped.
2. **Dynamic Sliding Windows:** Truncating conversational history based on the user-defined `compressionRatio`.
3. **Autonomous Bypass:** Rerouting specific payloads to alternative models without exposing secret API keys to the frontend client.

## 🚀 Setup & Execution

### Prerequisites
- Python 3.10+
- `uv` (Fast Python Package Manager)

### 1. HTTP Server (For Agent Desktop)
Runs the standard HTTP REST API on port `4000`.
```bash
# Install dependencies
uv pip install -r requirements.txt

# Run the server
uv run uvicorn main:app --host 0.0.0.0 --port 4000 --reload
```

### 2. Universal MCP Server
If you want to plug the RTK Engine into **Claude Desktop**, **Cursor**, or any other Model Context Protocol agent, you can attach it directly using the Stdio entrypoint:
```json
{
  "mcpServers": {
    "rtk-engine": {
      "command": "uv",
      "args": ["run", "mcp_server.py"],
      "cwd": "/path/to/rtk-engine"
    }
  }
}
```

### 3. Docker (Cloud API Deployment)
To host the RTK Engine on the cloud (Render, AWS, Heroku) so any agent on the internet can reach it:
```bash
docker build -t rtk-engine .
docker run -p 4000:4000 rtk-engine
```

## 📡 API Reference

### `POST /api/compress`
Compresses a chat timeline into an optimized payload.

**Request Body:**
```json
{
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ],
  "rtkConfig": {
    "enabled": true,
    "compressionRatio": 0.8,
    "slidingWindowSize": 4000
  }
}
```

**Response:**
```json
{
  "compressedMessages": [...],
  "stats": {
    "originalLength": 50,
    "compressedLength": 40,
    "compressionRatio": 0.8,
    "slidingWindowSize": 4000
  }
}
```

### `POST /api/proxy`
Securely proxies an LLM generation request.

**Request Body:**
```json
{
  "payload": "...",
  "rtkConfig": {
    "dynamicBypass": true,
    "modelRoute": "claude-3-5-sonnet"
  }
}
```

---
*Confidential Repository. Property of JWEB0689.*
