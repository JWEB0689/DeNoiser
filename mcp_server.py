from mcp.server.fastmcp import FastMCP
import json

# Initialize DeNoiser as a universal MCP Server
mcp = FastMCP("DeNoiser")

@mcp.tool()
def filter_command_output(command: str, raw_output: str) -> str:
    """
    Applies heuristic token-reduction filters to raw command output.
    This strips out noisy logs (like successful tests, verbose npm logs, etc)
    and massively reduces the token context size.
    
    Args:
        command: The command that produced the output (e.g., 'git status')
        raw_output: The raw text output from the command.
    """
    from filters.engine import engine
    try:
        filtered = engine.filter_output(command, raw_output)
        return json.dumps({
            "status": "success",
            "original_chars": len(raw_output),
            "filtered_chars": len(filtered),
            "filtered_output": filtered
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    # Start the server using standard Stdio (compatible with Claude Desktop, Cursor, etc)
    mcp.run(transport='stdio')
