<div align="center">
  <h1>DeNoiser (Python)</h1>
  <p><strong>Universal Token Compression CLI & MCP Server</strong></p>
  <img src="https://img.shields.io/badge/Python-CLI-blue?style=for-the-badge" alt="Stack" />
</div>

---

## Overview

**DeNoiser** is a high-performance Python CLI and MCP Server that filters and compresses command outputs before they reach your LLM context window. 

Instead of blindly sending thousands of lines of terminal noise to an LLM, DeNoiser applies heuristic filters to:
1. Strip out verbose logs, success messages, and boilerplate.
2. Isolate mistakes and errors.
3. Massively reduce token consumption for long-running autonomous sessions.

## ⚙️ How It Works

You can use the `denoiser` wrapper in front of any command.
```
  Without denoiser:                               With denoiser:

  LLM Agent  --git status-->  git                 LLM Agent  --git status-->  DeNoiser  -->  git
                                |                                                       |          |
          ~2,000 tokens (raw)   |                            ~200 tokens        | filter   |
  <-----------------------------+                 <------------- (filtered) ----+----------+
```

## 🚀 Setup & Execution

### Prerequisites
- Python 3.10+
- `uv` (Fast Python Package Manager)

### 1. Standalone Global CLI (Windows)
You can use the engine locally in your own terminal to wrap any noisy command!
1. Open your Windows Start Menu and search for **"Environment Variables"**.
2. Edit the **PATH** variable.
3. Add the absolute path to this folder.
4. Restart your terminal.

You can now prefix any massive command with `denoiser` (e.g., `denoiser npm install` or `denoiser git status`) from anywhere on your PC, and it will instantly filter the noise and print beautifully optimized output back to your screen!

### 2. Universal MCP Server
If you want to plug DeNoiser into **Claude Desktop**, **Cursor**, **Antigravity**, or any other Model Context Protocol agent, you can attach it directly using the Stdio entrypoint:

First, install dependencies:
```bash
uv pip install -r requirements.txt
```

Then configure your agent:
```json
{
  "mcpServers": {
    "denoiser": {
      "command": "uv",
      "args": ["run", "mcp_server.py"],
      "cwd": "/path/to/denoiser-repo"
    }
  }
}
```

This exposes the `filter_command_output` tool to your agent, allowing it to autonomously filter terminal output.

---
*Confidential Repository. Property of JWEB0689.*
