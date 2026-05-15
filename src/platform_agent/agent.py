"""Platform Agent - Uses SurrealQL for all operations + any LLM."""

import os
from surrealdb import AsyncSurreal
from .config import AgentConfig


# =============================================================================
# LLM Integration - Ollama compatible (self-hosted, open)
# =============================================================================

class LLM:
    """Ollama LLM integration - supports any open model."""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
    ):
        self.api_key = api_key  # Not used for Ollama, but for compatibility
        self.model = model
        self.base_url = base_url
    
    async def generate(self, messages: list, stream: bool = False) -> str:
        """Generate response from Ollama."""
        import aiohttp
        
        # Convert to Ollama format
        ollama_messages = []
        for msg in messages:
            # Map roles
            role = msg["role"]
            if role == "system":
                role = "system"
            elif role == "assistant":
                role = "assistant"
            else:
                role = "user"
            ollama_messages.append({
                "role": role,
                "content": msg["content"],
            })
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": stream,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
            ) as resp:
                data = await resp.json()
                return data["message"]["content"]
    
    async def generate_raw(self, prompt: str) -> str:
        """Simple generate (non-chat) for testing."""
        import aiohttp
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
            ) as resp:
                data = await resp.json()
                return data["response"]


class PlatformAgent:
    """Agent that uses SurrealQL + LLM."""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.db = None
        self.llm = LLM(api_key=config.llm_api_key if config else None)
    
    async def connect(self):
        self.db = AsyncSurreal(self.config.surrealdb_url)
        await self.db.connect()
        await self.db.use(
            namespace=self.config.surrealdb_namespace,
            database=self.config.surrealdb_database,
        )
        await self.db.signin({
            "username": self.config.surrealdb_username,
            "password": self.config.surrealdb_password,
        })
    
    async def close(self):
        if self.db:
            await self.db.close()
    
    # -------------------------------------------------------------------------
    # SurrealQL Operations
    # -------------------------------------------------------------------------
    
    async def think(self, query: str, stream: bool = False) -> str:
        """Process query using SurrealQL + LLM."""
        
        # Get conversation history from SurrealDB
        history = await self.db.query(
            "SELECT query, response FROM conversations ORDER BY timestamp DESC LIMIT 10"
        )
        
        # Build messages
        messages = [
            {"role": "system", "content": "You are Platform Agent, an AI assistant powered by SurrealDB."}
        ]
        
        # Add history
        for msg in reversed(history):
            messages.append({"role": "user", "content": msg.get("query", "")})
            messages.append({"role": "assistant", "content": msg.get("response", "")})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response = await self.llm.generate(messages)
        
        # Store conversation
        await self.db.create("conversations", {
            "query": query,
            "response": response,
            "timestamp": "time::now()",
        })
        
        return response
    
    async def remember(self, content: str, memory_type: str = "general") -> dict:
        """Store memory using SurrealQL."""
        return await self.db.create("memories", {
            "content": content,
            "type": memory_type,
            "timestamp": "time::now()",
        })
    
    async def recall(self, query: str, limit: int = 5) -> list:
        """Recall memories using SurrealQL."""
        return await self.db.query(
            f"SELECT * FROM memories WHERE content CONTAINS '{query}' LIMIT {limit}"
        )
    
    async def search(self, query: str, limit: int = 5) -> list:
        """Search using SurrealQL full-text."""
        return await self.db.query(
            f"SELECT * FROM documents WHERE content @1@ '{query}' LIMIT {limit}"
        )
    
    async def embed(self, texts: list) -> list:
        """Add documents using SurrealQL."""
        results = []
        for text in texts:
            r = await self.db.create("documents", {
                "content": text,
                "timestamp": "time::now()",
            })
            results.append(r)
        return results
    
    async def know(self, entity: str, entity_type: str, relations: list = None) -> dict:
        """Add entity using SurrealQL."""
        e = await self.db.create("entities", {
            "name": entity,
            "type": entity_type,
            "timestamp": "time::now()",
        })
        if relations:
            for rel in relations:
                await self.db.create("relations", {
                    "from": entity,
                    "to": rel.get("to"),
                    "type": rel.get("type"),
                })
        return e
    
    async def query_graph(self, entity: str) -> dict:
        """Query graph using SurrealQL."""
        return await self.db.query(
            f"SELECT *, ->relations AS rels FROM entities WHERE name = '{entity}'"
        )
    
    async def get_history(self, limit: int = 20) -> list:
        """Get history using SurrealQL."""
        return await self.db.query(
            f"SELECT * FROM conversations ORDER BY timestamp DESC LIMIT {limit}"
        )
    
    # -------------------------------------------------------------------------
    # Raw SurrealQL
    # -------------------------------------------------------------------------
    
    async def query(self, sql: str, vars: dict = None) -> list:
        """Execute raw SurrealQL."""
        return await self.db.query(sql, vars)
    
    async def create(self, table: str, data: dict) -> dict:
        """Create record using SurrealQL."""
        return await self.db.create(table, data)
    
    async def select(self, table: str) -> list:
        """Select records using SurrealQL."""
        return await self.db.select(table)


# Convenience
def create_agent(**kwargs) -> PlatformAgent:
    return PlatformAgent(AgentConfig(**kwargs))