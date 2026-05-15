"""Platform Agent - SurrealDB-native autonomous AI agent."""

import os
import json
from typing import Any, Optional, Generator, List
from datetime import datetime
from dataclasses import dataclass, field

import asyncio
from surrealdb import AsyncSurreal

from .config import AgentConfig
from .tools import Tool, FileTool, BashTool, SearchTool, ToolRegistry


# =============================================================================
# SurrealDB-native Embeddings
# =============================================================================

class SurrealEmbeddings:
    """SurrealDB-native vector embeddings.
    
    Uses SurrealDB's built-in vector search capabilities.
    """
    
    def __init__(
        self,
        db: AsyncSurreal,
        dimension: int = 1536,
        field_name: str = "embedding",
    ):
        self._db = db
        self._dimension = dimension
        self._field_name = field_name
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text.
        
        Note: In production, use OpenAI embeddings or similar.
        For now, returns a simple hash-based vector.
        """
        # Simple hash-based embedding (placeholder)
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        # Generate deterministic "embedding" from hash
        return [
            (b / 255.0) * 2 - 1
            for b in hash_bytes[:self._dimension]
        ]
    
    async def add_documents(
        self,
        texts: List[str],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Add documents with embeddings to SurrealDB."""
        results = []
        for i, text in enumerate(texts):
            embedding = await self.embed_text(text)
            doc_id = ids[i] if ids else f"doc_{datetime.now().timestamp()}_{i}"
            
            record = {
                "id": doc_id,
                "content": text,
                self._field_name: embedding,
                "metadata": metadata[i] if metadata else {},
                "created_at": datetime.now().isoformat(),
            }
            
            await self._db.create("documents", record)
            results.append(record)
        
        return results
    
    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[dict]:
        """Search documents by similarity."""
        query_embedding = await self.embed_text(query)
        
        # Use SurrealDB's vector search
        results = await self._db.query(
            f"""SELECT *, vector::distance(embedding, $query_emb) AS distance 
            FROM documents 
            ORDER BY distance ASC 
            LIMIT {limit}""",
            {"query_emb": query_embedding}
        )
        
        return results


# =============================================================================
# SurrealDB-native Agent Memory
# =============================================================================

class SurrealMemory:
    """Full SurrealDB-backed memory with native features.
    
    Collections:
    - conversations: Past interactions
    - memories: Stored memories  
    - documents: Full-text searchable docs
    - entities: Knowledge graph nodes
    - relations: Knowledge graph edges
    """
    
    def __init__(
        self,
        url: str,
        namespace: str = "platform",
        database: str = "agent",
        username: str = "root",
        password: str = "root",
    ):
        self.url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        self._db: Optional[AsyncSurreal] = None
        self._embeddings: Optional[SurrealEmbeddings] = None
        self._connected = False
    
    async def connect(self) -> "SurrealMemory":
        """Connect to SurrealDB."""
        self._db = AsyncSurreal(self.url)
        await self._db.connect()
        await self._db.use(namespace=self.namespace, database=self.database)
        await self._db.signin({"username": self.username, "password": self.password})
        self._embeddings = SurrealEmbeddings(self._db)
        self._connected = True
        
        # Ensure collections exist with schemas
        await self._ensure_collections()
        
        return self
    
    async def _ensure_collections(self):
        """Ensure collections exist with proper schemas."""
        schemas = [
            "DEFINE TABLE conversations SCHEMAFULL",
            "DEFINE FIELD query ON conversations TYPE string",
            "DEFINE FIELD response ON conversations TYPE string",
            "DEFINE FIELD timestamp ON conversations TYPE string",
            "DEFINE FIELD metadata ON conversations TYPE object",
            "",
            "DEFINE TABLE memories SCHEMAFULL", 
            "DEFINE FIELD content ON memories TYPE string",
            "DEFINE FIELD type ON memories TYPE string",
            "DEFINE FIELD importance ON memories TYPE float DEFAULT 0.5",
            "DEFINE FIELD metadata ON memories TYPE object",
            "DEFINE FIELD timestamp ON memories TYPE string",
            "",
            "DEFINE TABLE documents SCHEMAFULL",
            "DEFINE FIELD content ON documents TYPE string",
            "DEFINE FIELD embedding ON documents TYPE array",
            "DEFINE FIELD metadata ON documents TYPE object",
            "DEFINE FIELD created_at ON documents TYPE string",
            "",
            "DEFINE TABLE entities SCHEMAFULL",
            "DEFINE FIELD name ON entities TYPE string",
            "DEFINE FIELD type ON entities TYPE string",
            "DEFINE FIELD properties ON entities TYPE object",
            "DEFINE FIELD created_at ON entities TYPE string",
            "",
            "DEFINE TABLE relations SCHEMAFULL",
            "DEFINE FIELD from ON relations TYPE record(entities)",
            "DEFINE FIELD to ON relations TYPE record(entities)",
            "DEFINE FIELD type ON relations TYPE string",
            "DEFINE FIELD properties ON relations TYPE object",
            "DEFINE FIELD created_at ON relations TYPE string",
        ]
        
        for schema in schemas:
            if schema:
                try:
                    await self._db.query(schema)
                except Exception:
                    pass
    
    async def close(self):
        """Close connection."""
        if self._db:
            await self._db.close()
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    # -------------------------------------------------------------------------
    # Conversations
    # -------------------------------------------------------------------------
    
    async def add_conversation(
        self,
        query: str,
        response: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Store a conversation."""
        record = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        return await self._db.create("conversations", record)
    
    async def get_conversations(
        self,
        limit: int = 20,
    ) -> List[dict]:
        """Get recent conversations."""
        return await self._db.query(
            f"SELECT * FROM conversations ORDER BY timestamp DESC LIMIT {limit}"
        )
    
    async def search_conversations(
        self,
        query: str,
        limit: int = 5,
    ) -> List[dict]:
        """Search conversations (full-text)."""
        return await self._db.query(
            f"""SELECT * FROM conversations 
            WHERE query CONTAINS '{query}' OR response CONTAINS '{query}'
            ORDER BY timestamp DESC LIMIT {limit}"""
        )
    
    # -------------------------------------------------------------------------
    # Memories
    # -------------------------------------------------------------------------
    
    async def add_memory(
        self,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
    ) -> dict:
        """Store a memory."""
        record = {
            "content": content,
            "type": memory_type,
            "importance": importance,
            "metadata": {},
            "timestamp": datetime.now().isoformat(),
        }
        return await self._db.create("memories", record)
    
    async def get_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[dict]:
        """Get memories."""
        if memory_type:
            return await self._db.query(
                f"SELECT * FROM memories WHERE type = '{memory_type}' ORDER BY importance DESC LIMIT {limit}"
            )
        return await self._db.query(
            f"SELECT * FROM memories ORDER BY importance DESC LIMIT {limit}"
        )
    
    # -------------------------------------------------------------------------
    # Documents (Vector Search)
    # -------------------------------------------------------------------------
    
    async def add_documents(
        self,
        texts: List[str],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Add documents with vector embeddings."""
        if not self._embeddings:
            raise RuntimeError("Not connected")
        return await self._embeddings.add_documents(texts, ids, metadata)
    
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
    ) -> List[dict]:
        """Semantic search documents."""
        if not self._embeddings:
            raise RuntimeError("Not connected")
        return await self._embeddings.similarity_search(query, limit)
    
    # -------------------------------------------------------------------------
    # Knowledge Graph
    # -------------------------------------------------------------------------
    
    async def add_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[dict] = None,
    ) -> dict:
        """Add an entity."""
        record = {
            "name": name,
            "type": entity_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat(),
        }
        return await self._db.create("entities", record)
    
    async def add_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        properties: Optional[dict] = None,
    ) -> dict:
        """Add a relation between entities."""
        from_rec = await self._db.query(f"SELECT * FROM entities WHERE name = '{from_entity}' LIMIT 1")
        to_rec = await self._db.query(f"SELECT * FROM entities WHERE name = '{to_entity}' LIMIT 1")
        
        if not from_rec or not to_rec:
            raise ValueError(f"Entity not found: {from_entity} or {to_entity}")
        
        record = {
            "from": from_rec[0]["id"],
            "to": to_rec[0]["id"],
            "type": relation_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat(),
        }
        return await self._db.create("relations", record)
    
    async def get_entity(self, name: str) -> Optional[dict]:
        """Get an entity."""
        results = await self._db.query(f"SELECT * FROM entities WHERE name = '{name}' LIMIT 1")
        return results[0] if results else None
    
    async def get_relations(
        self,
        entity: Optional[str] = None,
    ) -> List[dict]:
        """Get relations."""
        if entity:
            return await self._db.query(
                f"SELECT * FROM relations WHERE from = '{entity}' OR to = '{entity}'"
            )
        return await self._db.select("relations")
    
    # -------------------------------------------------------------------------
    # Raw Query
    # -------------------------------------------------------------------------
    
    async def query(
        self,
        query: str,
        vars: Optional[dict] = None,
    ) -> List[dict]:
        """Run a raw SurrealQL query."""
        return await self._db.query(query, vars)


# =============================================================================
# Platform Agent (SurrealDB-native)
# =============================================================================

@dataclass
class PlatformAgent:
    """Autonomous Platform Agent with SurrealDB-native capabilities.
    
    Features (all SurrealDB-native):
    - Vector embeddings & similarity search
    - Full-text search (BM25)
    - Knowledge graph (entities & relations)
    - Time-series (timestamps)
    - Object-relational (nested records)
    """
    
    config: AgentConfig = field(default_factory=AgentConfig)
    _memory: Optional[SurrealMemory] = field(default=None, repr=False)
    _tools: ToolRegistry = field(default_factory=ToolRegistry)
    _conversation_history: list = field(default_factory=list)
    _initialized: bool = field(default=False, repr=False)
    
    async def initialize(self) -> "PlatformAgent":
        """Initialize the agent."""
        self._memory = SurrealMemory(
            url=self.config.surrealdb_url,
            namespace=self.config.surrealdb_namespace,
            database=self.config.surrealdb_database,
            username=self.config.surrealdb_username,
            password=self.config.surrealdb_password,
        )
        await self._memory.connect()
        self._initialized = True
        return self
    
    async def close(self):
        """Close connections."""
        if self._memory:
            await self._memory.close()
            self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    async def think(self, query: str) -> str:
        """Process a query."""
        if not self._initialized:
            return "Agent not initialized. Call initialize() first."
        
        # 1. Search memories
        memory_results = []
        try:
            memory_results = await self._memory.search_conversations(query)
        except Exception:
            pass
        
        # 2. Build context
        context = self._build_context(memory_results)
        
        # 3. Generate response
        response = f"Platform Agent: {query}\n\n"
        if context:
            response += f"Context: {context[:200]}..."
        
        # 4. Store
        await self._memory.add_conversation(query, response)
        
        return response
    
    def _build_context(self, memories: List[dict]) -> str:
        if not memories:
            return ""
        return "\n".join([
            f"Q: {m.get('query', '')[:100]} A: {m.get('response', '')[:100]}"
            for m in memories[:3]
        ])
    
    # -------------------------------------------------------------------------
    # High-level API
    # -------------------------------------------------------------------------
    
    async def remember(
        self,
        content: str,
        memory_type: str = "general",
    ) -> dict:
        """Store a memory."""
        return await self._memory.add_memory(content, memory_type)
    
    async def recall(
        self,
        query: str,
        limit: int = 5,
    ) -> List[dict]:
        """Recall memories."""
        return await self._memory.get_memories(limit=limit)
    
    async def embed(
        self,
        documents: List[str],
    ) -> List[dict]:
        """Add documents for semantic search."""
        return await self._memory.add_documents(documents)
    
    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[dict]:
        """Semantic search."""
        return await self._memory.search_documents(query, limit)
    
    async def know(
        self,
        entity: str,
        entity_type: str,
        relations: Optional[List[dict]] = None,
    ) -> dict:
        """Add knowledge to graph."""
        entity_rec = await self._memory.add_entity(entity, entity_type)
        if relations:
            for rel in relations:
                await self._memory.add_relation(
                    from_entity=entity,
                    to_entity=rel["to"],
                    relation_type=rel["type"],
                )
        return entity_rec
    
    async def query_graph(
        self,
        entity: str,
    ) -> dict:
        """Query knowledge graph."""
        entity = await self._memory.get_entity(entity)
        if entity:
            entity["relations"] = await self._memory.get_relations(entity=entity)
        return entity
    
    async def get_history(self, limit: int = 20) -> List[dict]:
        """Get conversation history."""
        return await self._memory.get_conversations(limit)


# =============================================================================
# Sync Wrapper
# =============================================================================

class SyncPlatformAgent:
    """Synchronous wrapper."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self._config = config or AgentConfig()
        self._agent: Optional[PlatformAgent] = None
    
    def start(self) -> "SyncPlatformAgent":
        self._agent = PlatformAgent(config=self._config)
        asyncio.run(self._agent.initialize())
        return self
    
    def think(self, query: str) -> str:
        if not self._agent:
            self.start()
        return asyncio.run(self._agent.think(query))
    
    def stop(self):
        if self._agent:
            asyncio.run(self._agent.close())


def create_agent(**kwargs) -> SyncPlatformAgent:
    """Create a Platform Agent."""
    config = AgentConfig(**kwargs)
    return SyncPlatformAgent(config=config)