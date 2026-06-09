from mcp.server.fastmcp import FastMCP
import json

# Initialize the RTK Engine as a universal MCP Server
mcp = FastMCP("RTK Engine")

@mcp.tool()
def compress_context(messages_json: str, compression_ratio: float = 0.8, sliding_window_size: int = 4000) -> str:
    """
    Compress a conversational token window using the RTK sliding-window heuristic.
    
    Args:
        messages_json: A JSON string representation of the chat timeline (list of message dicts with 'role' and 'content').
        compression_ratio: The percentage of recent interaction history to keep (e.g. 0.8 keeps 80%).
        sliding_window_size: The token window limit (metadata placeholder).
    """
    try:
        messages = json.loads(messages_json)
        
        # 1. Always keep system prompts
        system_messages = [m for m in messages if m.get("role") == "system"]
        
        # 2. Extract recent interaction history
        conversation_messages = [m for m in messages if m.get("role") != "system"]
        
        # Simple sliding window heuristic
        window_count = max(1, int(len(conversation_messages) * compression_ratio))
        recent_messages = conversation_messages[-window_count:] if window_count > 0 else []
        
        compressed_messages = system_messages + recent_messages
        
        return json.dumps({
            "status": "success",
            "stats": {
                "originalLength": len(messages),
                "compressedLength": len(compressed_messages),
                "compressionRatio": compression_ratio
            },
            "compressedMessages": compressed_messages
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

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
        filtered = engine.filter_output(raw_output)
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
