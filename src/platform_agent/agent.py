"""Platform Agent - Autonomous AI agent with SurrealDB backend."""

import os
import json
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

import asyncio
from surrealdb import AsyncSurreal

from .config import AgentConfig
from .memory import AgentMemory
from .tools import Tool, FileTool, BashTool, SearchTool


@dataclass
class AgentMemory:
    """Memory system backed by SurrealDB."""
    
    url: str
    namespace: str = "platform"
    database: str = "agent"
    username: str = "root"
    password: str = "root"
    
    _db: Optional[AsyncSurreal] = field(default=None, repr=False)
    
    async def connect(self) -> "AgentMemory":
        """Connect to SurrealDB."""
        self._db = AsyncSurreal(self.url)
        await self._db.connect()
        await self._db.use(namespace=self.namespace, database=self.database)
        await self._db.signin({"username": self.username, "password": self.password})
        return self
    
    async def close(self) -> None:
        """Close connection."""
        if self._db:
            await self._db.close()
    
    async def create(
        self, 
        collection: str, 
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a record."""
        return await self._db.create(collection, data)
    
    async def select(self, collection: str) -> list[dict[str, Any]]:
        """Select all records from a collection."""
        return await self._db.select(collection)
    
    async def query(
        self, 
        query: str, 
        vars: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Run a query."""
        return await self._db.query(query, vars)


@dataclass
class PlatformAgent:
    """Autonomous Platform Agent with SurrealDB backend.
    
    Features:
    - Persistent memory storage
    - Vector search for semantic retrieval
    - Knowledge graph for reasoning
    - Tool execution capabilities
    - Full-text search
    """
    
    config: AgentConfig = field(default_factory=AgentConfig)
    _memory: Optional[AgentMemory] = field(default=None, repr=False)
    _tools: list[Tool] = field(default_factory=list)
    _conversation_history: list[dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default tools."""
        self._tools = [
            FileTool(),
            BashTool(),
            SearchTool(),
        ]
    
    async def initialize(self) -> "PlatformAgent":
        """Initialize the agent."""
        self._memory = AgentMemory(
            url=self.config.surrealdb_url,
            namespace=self.config.surrealdb_namespace,
            database=self.config.surrealdb_database,
            username=self.config.surrealdb_username,
            password=self.config.surrealdb_password,
        )
        await self._memory.connect()
        return self
    
    async def close(self) -> None:
        """Close connections."""
        if self._memory:
            await self._memory.close()
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent."""
        self._tools.append(tool)
    
    async def think(self, query: str) -> str:
        """Process a query.
        
        Args:
            query: User query
            
        Returns:
            Agent response
        """
        # Search memory for context
        memory_results = await self._search_memory(query)
        
        # Build context
        context = self._build_context(memory_results)
        
        # Use LLM to generate response
        response = await self._generate_response(query, context)
        
        # Store interaction
        await self._store_interaction(query, response)
        
        return response
    
    async def _search_memory(self, query: str) -> list[dict[str, Any]]:
        """Search agent memory."""
        results = []
        try:
            if self._memory:
                # Query recent conversations
                results = await self._memory.query(
                    "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT 10"
                )
        except Exception as e:
            if self.config.verbose:
                print(f"Memory search error: {e}")
        return results
    
    def _build_context(self, memory_results: list[dict[str, Any]]) -> str:
        """Build context from memory."""
        if not memory_results:
            return ""
        
        context_parts = ["Recent context:"]
        for i, result in enumerate(memory_results[:5]):
            q = result.get("query", "")
            a = result.get("response", "")
            if q and a:
                context_parts.append(f"\n{i+1}. Q: {q[:100]}...")
                context_parts.append(f"   A: {a[:100]}...")
        
        return "\n".join(context_parts[:5])
    
    async def _generate_response(self, query: str, context: str) -> str:
        """Generate response using LLM."""
        # Placeholder - in production, connect to OpenAI/Anthropic
        # For now, return a simple acknowledgment
        response = f"Platform Agent received: {query}"
        
        if context:
            response += f"\n\n(Context: found {len(context.split(chr(10)))} items)"
        
        return response
    
    async def _store_interaction(self, query: str, response: str) -> None:
        """Store interaction in memory."""
        if not self._memory:
            return
        
        try:
            await self._memory.create("conversations", {
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            if self.config.verbose:
                print(f"Storage error: {e}")
        
        # Update local history
        self._conversation_history.append({"role": "user", "content": query})
        self._conversation_history.append({"role": "assistant", "content": response})
    
    async def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get conversation history."""
        if not self._memory:
            return []
        return await self._memory.query(
            f"SELECT * FROM conversations ORDER BY timestamp DESC LIMIT {limit}"
        )
    
    async def clear_history(self) -> None:
        """Clear conversation history."""
        if self._memory:
            await self._memory.query("DELETE FROM conversations")
        self._conversation_history = []


class SyncPlatformAgent:
    """Synchronous wrapper for PlatformAgent."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self._config = config or AgentConfig()
        self._agent: Optional[PlatformAgent] = None
    
    def start(self) -> "SyncPlatformAgent":
        """Start the agent (sync wrapper)."""
        self._agent = PlatformAgent(config=self._config)
        asyncio.run(self._agent.initialize())
        return self
    
    def think(self, query: str) -> str:
        """Process a query synchronously."""
        if not self._agent:
            self.start()
        return asyncio.run(self._agent.think(query))
    
    def stop(self) -> None:
        """Stop the agent."""
        if self._agent:
            asyncio.run(self._agent.close())


# Convenience function
def create_agent(**kwargs) -> SyncPlatformAgent:
    """Create a Platform Agent.
    
    Usage:
        agent = create_agent(
            surrealdb_url="ws://localhost:8000/rpc",
        )
        response = agent.think("Hello!")
    """
    config = AgentConfig(**kwargs)
    return SyncPlatformAgent(config=config)