"""Platform Agent Memory - SurrealDB-backed memory system."""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from surrealdb import AsyncSurreal


@dataclass
class AgentMemory:
    """Memory system backed by SurrealDB.
    
    Provides:
    - Conversation storage
    - Vector embeddings for semantic search
    - Knowledge graph storage
    - Full-text search
    """
    
    url: str
    namespace: str = "platform"
    database: str = "agent"
    username: str = "root"
    password: str = "root"
    
    _db: Optional[AsyncSurreal] = field(default=None, repr=False)
    _connected: bool = field(default=False, repr=False)
    
    async def connect(self) -> "AgentMemory":
        """Connect to SurrealDB."""
        self._db = AsyncSurreal(self.url)
        await self._db.connect()
        await self._db.use(namespace=self.namespace, database=self.database)
        await self._db.signin({"username": self.username, "password": self.password})
        self._connected = True
        return self
    
    async def close(self) -> None:
        """Close connection."""
        if self._db:
            await self._db.close()
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
    
    # -------------------------------------------------------------------------
    # Conversation Memory
    # -------------------------------------------------------------------------
    
    async def add_conversation(
        self,
        query: str,
        response: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Add a conversation to memory.
        
        Args:
            query: User query
            response: Agent response
            metadata: Optional additional metadata
            
        Returns:
            Created record
        """
        data = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        return await self._db.create("conversations", data)
    
    async def get_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get conversation history.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of conversations
        """
        return await self._db.query(
            f"SELECT * FROM conversations ORDER BY timestamp DESC LIMIT {limit} START {offset}"
        )
    
    async def search_conversations(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search conversations by content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching conversations
        """
        return await self._db.query(
            f"SELECT * FROM conversations WHERE query CONTAINS '{query}' OR response CONTAINS '{query}' LIMIT {limit}"
        )
    
    async def clear_conversations(self) -> None:
        """Clear all conversations."""
        await self._db.query("DELETE FROM conversations")
    
    # -------------------------------------------------------------------------
    # Vector/Memory Storage
    # -------------------------------------------------------------------------
    
    async def add_memory(
        self,
        content: str,
        memory_type: str = "general",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Add a memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory (general, important, etc.)
            metadata: Optional metadata
            
        Returns:
            Created record
        """
        data = {
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        return await self._db.create("memories", data)
    
    async def get_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get memories.
        
        Args:
            memory_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of memories
        """
        if memory_type:
            return await self._db.query(
                f"SELECT * FROM memories WHERE type = '{memory_type}' ORDER BY timestamp DESC LIMIT {limit}"
            )
        return await self._db.query(
            f"SELECT * FROM memories ORDER BY timestamp DESC LIMIT {limit}"
        )
    
    async def search_memories(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search memories by content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching memories
        """
        return await self._db.query(
            f"SELECT * FROM memories WHERE content CONTAINS '{query}' LIMIT {limit}"
        )
    
    # -------------------------------------------------------------------------
    # Knowledge Graph
    # -------------------------------------------------------------------------
    
    async def add_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Add an entity to the knowledge graph.
        
        Args:
            name: Entity name
            entity_type: Type of entity
            properties: Optional properties
            
        Returns:
            Created entity
        """
        data = {
            "name": name,
            "type": entity_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat(),
        }
        return await self._db.create("entities", data)
    
    async def add_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Add a relation between entities.
        
        Args:
            from_entity: Source entity name
            to_entity: Target entity name
            relation_type: Type of relation
            properties: Optional properties
            
        Returns:
            Created relation
        """
        data = {
            "from": from_entity,
            "to": to_entity,
            "type": relation_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat(),
        }
        return await self._db.create("relations", data)
    
    async def get_entity(self, name: str) -> Optional[dict[str, Any]]:
        """Get an entity by name.
        
        Args:
            name: Entity name
            
        Returns:
            Entity or None
        """
        results = await self._db.query(f"SELECT * FROM entities WHERE name = '{name}' LIMIT 1")
        return results[0] if results else None
    
    async def get_relations(
        self,
        entity: Optional[str] = None,
        relation_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get relations.
        
        Args:
            entity: Filter by entity (from or to)
            relation_type: Filter by relation type
            
        Returns:
            List of relations
        """
        if entity and relation_type:
            return await self._db.query(
                f"SELECT * FROM relations WHERE (from = '{entity}' OR to = '{entity}') AND type = '{relation_type}'"
            )
        if entity:
            return await self._db.query(
                f"SELECT * FROM relations WHERE from = '{entity}' OR to = '{entity}'"
            )
        if relation_type:
            return await self._db.query(
                f"SELECT * FROM relations WHERE type = '{relation_type}'"
            )
        return await self._db.select("relations")
    
    # -------------------------------------------------------------------------
    # Document Storage
    # -------------------------------------------------------------------------
    
    async def add_document(
        self,
        title: str,
        content: str,
        document_type: str = "note",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Add a document.
        
        Args:
            title: Document title
            content: Document content
            document_type: Type of document
            metadata: Optional metadata
            
        Returns:
            Created document
        """
        data = {
            "title": title,
            "content": content,
            "type": document_type,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        return await self._db.create("documents", data)
    
    async def get_documents(
        self,
        document_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get documents.
        
        Args:
            document_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of documents
        """
        if document_type:
            return await self._db.query(
                f"SELECT * FROM documents WHERE type = '{document_type}' ORDER BY updated_at DESC LIMIT {limit}"
            )
        return await self._db.query(
            f"SELECT * FROM documents ORDER BY updated_at DESC LIMIT {limit}"
        )
    
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search documents by content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching documents
        """
        return await self._db.query(
            f"SELECT * FROM documents WHERE title CONTAINS '{query}' OR content CONTAINS '{query}' LIMIT {limit}"
        )
    
    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    
    async def query(
        self,
        query: str,
        vars: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Run a raw query.
        
        Args:
            query: SurrealQL query
            vars: Query variables
            
        Returns:
            Query results
        """
        return await self._db.query(query, vars)
    
    async def create(
        self,
        collection: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a record in a collection.
        
        Args:
            collection: Collection name
            data: Record data
            
        Returns:
            Created record
        """
        return await self._db.create(collection, data)
    
    async def delete(
        self,
        collection: str,
        query: str,
    ) -> list[dict[str, Any]]:
        """Delete records.
        
        Args:
            collection: Collection name
            query: Delete query
            
        Returns:
            Deleted records
        """
        return await self._db.query(f"DELETE {collection} {query}")


# Synchronous wrapper
class SyncAgentMemory:
    """Synchronous wrapper for AgentMemory."""
    
    def __init__(self, *args, **kwargs):
        import asyncio
        self._loop = asyncio.new_event_loop()
        self._memory = AgentMemory(*args, **kwargs)
    
    def __enter__(self):
        import asyncio
        self._loop.run_until_complete(self._memory.connect())
        return self
    
    def __exit__(self, *args):
        self._loop.run_until_complete(self._memory.close())
        self._loop.close()
    
    def __getattr__(self, name):
        import asyncio
        attr = getattr(self._memory, name)
        if asyncio.iscoroutinefunction(attr):
            def wrapper(*args, **kwargs):
                return self._loop.run_until_complete(attr(*args, **kwargs))
            return wrapper
        return attr