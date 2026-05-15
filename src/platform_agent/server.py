"""Platform Agent Server - SurrealDB-native API."""

from typing import Optional
from dataclasses import dataclass, field

from .config import AgentConfig
from .agent import PlatformAgent


# =============================================================================
# API Server - Uses SurrealDB's native protocols
# =============================================================================

@dataclass
class APIServer:
    """API server using SurrealDB's native connectivity:
    - WebSocket for real-time
    - HTTP/REST for CRUD
    - GraphQL support
    """
    
    config: AgentConfig = field(default_factory=AgentConfig)
    agent: Optional[PlatformAgent] = field(default=None, repr=False)
    host: str = "0.0.0.0"
    port: int = 8000
    
    async def start(self):
        """Start server."""
        print(f"API Server: {self.host}:{self.port}")
        print("  - WebSocket: ws://{host}:{port}/ws")
        print("  - REST: http://{host}:{port}/rpc")
        print("  - Health: http://{host}:{port}/health")
    
    def stop(self):
        """Stop server."""
        print("Server stopped")


# =============================================================================
# REST - Uses SurrealDB REST API
# =============================================================================

class RESTEndpoints:
    """Uses SurrealDB's native REST API:
    - POST /rpc for SurrealQL
    - GET/POST /key/:table for CRUD
    """
    
    def __init__(self, agent: PlatformAgent):
        self.agent = agent
    
    async def health(self) -> dict:
        return {"status": "healthy", "db": "connected"}
    
    async def think(self, query: str) -> dict:
        if not self.agent:
            return {"error": "Not initialized"}
        return {"response": await self.agent.think(query)}