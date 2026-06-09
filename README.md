<div align="center">
  <h1>DeNoiser</h1>
  <p><strong>Universal Token Compression CLI & MCP Server for LLM Agents</strong></p>
  <img src="https://img.shields.io/badge/Python-CLI-blue?style=for-the-badge" alt="Stack" />
</div>

---

## 🛑 The Problem

When coding with AI Agents (like Claude Code, Cursor, Antigravity, etc.), running background terminal commands consumes **massive amounts of context tokens**. Commands like `npm install`, `git status`, or large test suites (`pytest`, `jest`) spit out thousands of lines of verbose logs, success indicators, and progress bars. 

Blindly feeding this noise into the LLM context window leads to:
- **Exploding API Costs:** Wasting tokens on useless boilerplate.
- **Context Degradation:** The LLM "forgets" important instructions because its context is flooded with terminal noise.

## 💡 The Solution

**DeNoiser** is a high-performance Python utility that intercepts and heuristically filters command outputs *before* they reach your LLM.

1. **Strips Noise:** Automatically drops progress bars, `npm` warnings, success checks, and verbose build logs.
2. **Isolates Errors:** If a command fails, DeNoiser specifically hunts down the Exception/Traceback and extracts *only* the error lines, ensuring your agent instantly sees the problem without the bloat.
3. **Saves Tokens:** Routinely reduces terminal output token consumption by **60-90%**.

```text
  Without denoiser:                               With denoiser:

  LLM Agent  --git status-->  git                 LLM Agent  --git status-->  DeNoiser  -->  git
                                |                                                       |          |
          ~2,000 tokens (raw)   |                            ~200 tokens        | filter   |
  <-----------------------------+                 <------------- (filtered) ----+----------+
```

---

## 🚀 Installation

You don't even need Python installed to use DeNoiser. You can download the pre-compiled, standalone executable directly from GitHub Releases!

1. Go to the **Releases** page on this repository.
2. Download the binary for your operating system:
   - **Windows:** `denoiser-windows.exe`
   - **macOS:** `denoiser-macos`
   - **Linux:** `denoiser-linux`
3. Rename the downloaded file to just `denoiser` (or `denoiser.exe` on Windows).
4. Move it into a directory that is in your system's `PATH` (e.g., `C:\Program Files\DeNoiser` or `~/.local/bin`).

*Alternatively, you can clone this repo and use the `denoiser.bat` wrapper if you prefer running it directly from the Python source!*

---

## 🛠️ Usage (Standalone CLI)

Using DeNoiser is incredibly simple. Just prefix any noisy command with `denoiser`.

**Example 1: Package Managers**
```bash
denoiser npm install react
```
*(DeNoiser will drop the hundreds of lines of `npm WARN` and `added X packages` lines, returning only critical failures if they occur).*

**Example 2: Testing Frameworks**
```bash
denoiser pytest tests/
```
*(DeNoiser strips all the `test_xyz... ok` lines. If a test fails, it extracts ONLY the traceback!)*

---

## 🔌 Usage (MCP Server)

If you want to plug DeNoiser directly into an agent that supports the **Model Context Protocol (MCP)**, you can attach it as a server to expose the native `filter_command_output` tool to the LLM.

First, install the required dependencies using `uv` or `pip`:
```bash
pip install -r requirements.txt
```

Then configure your agent (e.g., in Claude Desktop's `claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "denoiser": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/DeNoiser"
    }
  }
}
```

This grants the AI agent the autonomous ability to run the DeNoiser filtering algorithm on any text block it wants to compress!

---
*Confidential Repository. Property of JWEB0689.*
