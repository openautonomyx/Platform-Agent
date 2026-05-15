# Platform Agent

SurrealQL-based autonomous agent.

## Features (Uses SurrealQL)

| Feature | SurrealQL | Description |
|---------|-----------|-------------|
| **ACID** | ✅ | Transactions |
| **Schema** | ✅ | SCHEMAFULL/SCHEMALESS |
| **Relations** | ✅ | Record links |
| **Events** | ✅ | DEFINE EVENT |
| **Live Queries** | ✅ | LIVE SELECT |
| **Temporal** | ✅ | VERSION, time travel |
| **Versioning** | ✅ | Immutable history |
| **Vector Search** | ✅ | HNSW, cosine/euclidean/manhattan |
| **Full-Text** | ✅ | BM25, analyzers |
| **Hybrid Search** | ✅ | Vector + full-text RRF |
| **SurrealQL** | ✅ | SELECT, CREATE, UPDATE, RELATE |
| **Graph** | ✅ | ->traverse, RELATE |
| **Functions** | ✅ | math, string, array, vector |
| **File Storage** | ✅ | DEFINE BUCKET, file::put/get |
| **Multi-tenancy** | ✅ | Namespaces, databases |
| **Embedded** | ✅ | In-memory, WASM, edge |
| **Change Data Capture** | ✅ | SHOW CHANGES |

## Install

```bash
pip install platform-agent
```

## Quick Start

```python
from platform_agent import PlatformAgent

agent = PlatformAgent()
await agent.connect()
await agent.think("Hello!")
await agent.close()
```

## SurrealQL Operations

All operations use SurrealQL:

```python
# Memory
await agent.remember("fact", "important")
await agent.recall("fact")

# Search  
await agent.search("query")
await agent.embed(["docs"])

# Knowledge
await agent.know("Python", "language", [{"to": "Guido", "type": "creator"}])
await agent.query_graph("Python")

# Raw SurrealQL
await agent.query("SELECT * FROM memories")
```