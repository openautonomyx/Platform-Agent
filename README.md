# Platform Agent

<p align="center">
  <img src="https://img.shields.io/pypi/v/platform-agent.svg" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/platform-agent.svg" alt="Python">
  <img src="https://img.shields.io/github/license/openautonomyx/Platform-Agent.svg" alt="License">
</p>

> An autonomous AI agent platform with **SurrealDB-native** storage

## Features (All SurrealDB-native)

| Feature | SurrealDB Native | Description |
|---------|-----------------|-------------|
| **💾 Memory** | ✅ | Persistent conversation storage |
| **🔍 Vector Search** | ✅ | Native vector embeddings & similarity |
| **🧠 Knowledge Graph** | ✅ | Entities & relations |
| **📝 Full-Text Search** | ✅ | BM25 search |
| **⏱️ Time-Series** | ✅ | Timestamped records |
| **🔗 Relations** | ✅ | Nested record relationships |

## Installation

```bash
# Using pip
pip install platform-agent

# Using uv (recommended)
uv add platform-agent
```

## Quick Start

```python
from platform_agent import PlatformAgent, AgentConfig

# Create configuration
config = AgentConfig(
    surrealdb_url="ws://localhost:8000/rpc",
    surrealdb_username="root",
    surrealdb_password="root",
)

# Create and initialize agent
agent = PlatformAgent(config=config)
await agent.initialize()

# Interact with the agent
response = await agent.think("Hello! How are you?")
print(response)

# Close connection
await agent.close()
```

### Using SurrealDB Docker

```bash
# Start SurrealDB
docker run -p 8000:8000 surrealdb/surrealdb:latest start --user root --pass root
```

## SurrealDB-Native Features

### 1. Memory (Conversations)

```python
# Store a memory
await agent.remember("User prefers Python", memory_type="preference")

# Recall memories
memories = await agent.recall("Python", limit=5)
```

### 2. Vector Search (Embeddings)

```python
# Add documents for semantic search
await agent.embed([
    "Python is a programming language",
    "JavaScript is for web development",
])

# Semantic search
results = await agent.search("programming languages")
```

### 3. Knowledge Graph

```python
# Add entity with relations
await agent.know(
    entity="Python",
    entity_type="language",
    relations=[
        {"to": "Guido van Rossum", "type": "created_by"},
        {"to": "1991", "type": "released_in"},
    ]
)

# Query entity
entity = await agent.query_graph("Python")
# Returns: {name: "Python", type: "language", relations: [...]}
```

### 4. Full-Text Search

```python
# Conversations are searchable
results = await agent._memory.search_conversations("hello")
```

## Configuration

### Environment Variables

```bash
# .env
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NAMESPACE=platform
SURREALDB_DATABASE=agent
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=root
```

### Config Options

| Setting | Description | Default |
|---------|-------------|---------|
| `surrealdb_url` | SurrealDB WebSocket URL | `ws://localhost:8000/rpc` |
| `surrealdb_namespace` | Database namespace | `platform` |
| `surrealdb_database` | Database name | `agent` |
| `surrealdb_username` | Username | `root` |
| `surrealdb_password` | Password | `root` |

## Architecture

```
┌─────────────────────────────────────┐
│         Platform Agent               │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  │
│  │   Think   │  │   Memory    │  │
│  │  Process  │──│(SurrealDB)  │  │
│  └─────────────┘  └──────────────┘  │
│       │                │           │
│       ▼                ▼           │
│  ┌─────────────────────────────┐  │
│  │   SurrealDB Collections    │  │
│  │  • conversations          │  │
│  │  • memories             │  │
│  │  • documents (vectors)   │  │
│  │  • entities (graph)     │  │
│  │  • relations (edges)   │  │
│  └─────────────────────────────┘  │
└─────────────────────────────────────┘
```

## API Reference

### PlatformAgent

```python
agent = PlatformAgent(config)
await agent.initialize()

# Core
response = await agent.think(query)
history = await agent.get_history(limit=20)

# Memory
await agent.remember(content, memory_type="general")
memories = await agent.recall(query, limit=5)

# Vector Search  
await agent.embed(["documents..."])
results = await agent.search(query, limit=5)

# Knowledge Graph
await agent.know(entity, entity_type, relations)
entity = await agent.query_graph(entity_name)

await agent.close()
```

## License

MIT License - see [LICENSE](LICENSE) for details.