import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="RTK Engine API")

# Allow CORS so Agent Desktop can communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RTKConfig(BaseModel):
    enabled: bool = False
    compressionRatio: float = 0.8
    slidingWindowSize: int = 4000
    dynamicBypass: bool = False
    modelRoute: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str
    id: Optional[str] = None
    timestamp: Optional[str] = None
    attachedFiles: Optional[List[str]] = None
    toolCall: Optional[Dict[str, Any]] = None

class CompressRequest(BaseModel):
    messages: List[Message]
    rtkConfig: RTKConfig

class ProxyRequest(BaseModel):
    payload: str
    rtkConfig: RTKConfig

class FilterRequest(BaseModel):
    command: Optional[str] = None
    raw_output: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "rtk-engine", "version": "1.0.0"}

@app.post("/api/compress")
def compress_context(req: CompressRequest):
    messages = req.messages
    config = req.rtkConfig

    if not config.enabled:
        return {
            "compressedMessages": [m.dict() for m in messages],
            "stats": {"originalLength": len(messages), "compressedLength": len(messages), "compressionRatio": 0}
        }

    print(f"[RTK-ENGINE] Received compression request: window={config.slidingWindowSize}, ratio={config.compressionRatio}")

    # 1. Always keep system prompts
    system_messages = [m for m in messages if m.role == "system"]

    # 2. Extract recent interaction history
    conversation_messages = [m for m in messages if m.role != "system"]

    # Simple sliding window heuristic
    window_count = max(1, int(len(conversation_messages) * config.compressionRatio))
    recent_messages = conversation_messages[-window_count:] if window_count > 0 else []

    compressed_messages = system_messages + recent_messages

    print(f"[RTK-ENGINE] Compressed {len(messages)} messages down to {len(compressed_messages)} messages.")

    return {
        "compressedMessages": [m.dict(exclude_none=True) for m in compressed_messages],
        "stats": {
            "originalLength": len(messages),
            "compressedLength": len(compressed_messages),
            "compressionRatio": config.compressionRatio,
            "slidingWindowSize": config.slidingWindowSize
        }
    }

@app.post("/api/proxy")
async def proxy_bypass(req: ProxyRequest):
    if not req.rtkConfig.dynamicBypass:
        raise HTTPException(status_code=400, detail="Autonomous Bypass is disabled")

    print(f"[RTK-ENGINE] Routing autonomous proxy payload via: {req.rtkConfig.modelRoute}")

    # Simulated proxy delay
    await asyncio.sleep(0.5)

    return {
        "status": "success",
        "provider": req.rtkConfig.modelRoute,
        "response": f"Simulated proxy response from {req.rtkConfig.modelRoute}. In a production environment, this engine will forward the payload using proprietary API keys hidden from the frontend client."
    }

@app.post("/api/filter")
def filter_output(req: FilterRequest):
    from filters.engine import engine
    filtered = engine.filter_output(req.raw_output)
    
    return {
        "status": "success",
        "original_length": len(req.raw_output),
        "filtered_length": len(filtered),
        "filtered_output": filtered
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=4000, reload=True)
