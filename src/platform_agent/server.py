"""Platform Agent - FastAPI server."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent import PlatformAgent, AgentConfig

app = FastAPI(title="Platform Agent")

config = AgentConfig.from_env()
agent = PlatformAgent(config)


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    response: str


class MemoryRequest(BaseModel):
    content: str
    memory_type: str = "general"


@app.on_event("startup")
async def startup():
    await agent.connect()


@app.on_event("shutdown")
async def shutdown():
    await agent.close()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        response = await agent.think(req.message, req.stream)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory")
async def add_memory(req: MemoryRequest):
    try:
        result = await agent.remember(req.content, req.memory_type)
        return {"ok": True, "memory": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories")
async def get_memories():
    try:
        memories = await agent.recall("", limit=20)
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}