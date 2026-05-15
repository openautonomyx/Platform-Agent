"""Platform Agent - Uses SurrealQL for all operations."""

from surrealdb import AsyncSurreal
from .config import AgentConfig


class PlatformAgent:
    """Agent that uses SurrealQL for all operations."""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.db = None
    
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
    
    async def think(self, query: str) -> str:
        """Process query using SurrealQL."""
        # Store conversation
        await self.db.create("conversations", {
            "query": query,
            "response": f"Agent: {query}",
            "timestamp": "time::now()",
        })
        return f"Agent: {query}"
    
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