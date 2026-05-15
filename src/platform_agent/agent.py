"""Platform Agent - Uses SurrealQL for all operations + configurable LLM."""

import os
from surrealdb import AsyncSurreal
from .config import AgentConfig


# =============================================================================
# LLM Integration - Configurable to any LLM provider
# =============================================================================

class LLM:
    """Configurable LLM - supports any provider."""
    
    PROVIDERS = {
        "ollama": "http://localhost:11434",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "lmstudio": "http://localhost:1234/v1",
        "litellm": "http://localhost:4000",
    }
    
    def __init__(
        self,
        provider: str = "ollama",
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.provider = provider
        self.model = model or self._default_model(provider)
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or self.PROVIDERS.get(provider, self.PROVIDERS["ollama"])
    
    def _default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            "ollama": "llama3",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
            "lmstudio": "llama3",
            "litellm": "gpt-4o-mini",
        }
        return defaults.get(provider, "llama3")
    
    async def generate(self, messages: list) -> str:
        """Generate response based on provider."""
        if self.provider == "ollama":
            return await self._ollamaChat(messages)
        elif self.provider == "openai":
            return await self._openaiChat(messages)
        elif self.provider == "anthropic":
            return await self._anthropicChat(messages)
        else:
            return await self._ollamaChat(messages)
    
    async def _ollamaChat(self, messages: list) -> str:
        """Ollama chat."""
        import ollama
        client = ollama.Client(self.base_url)
        
        response = client.chat(model=self.model, messages=messages)
        return response["message"]["content"]
    
    async def _openaiChat(self, messages: list) -> str:
        """OpenAI chat."""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={"model": self.model, "messages": messages},
            ) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    
    async def _anthropicChat(self, messages: list) -> str:
        """Anthropic chat."""
        import aiohttp
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        # Convert messages to Anthropic format
        system = ""
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": [m for m in messages if m.get("role") != "system"],
                    "system": system,
                },
            ) as resp:
                data = await resp.json()
                return data["content"][0]["text"]
    
    async def generate_raw(self, prompt: str) -> str:
        """Simple generate."""
        return await self.generate([{"role": "user", "content": prompt}])


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