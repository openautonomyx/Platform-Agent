# Platform Agent

<p align="center">
  <img src="https://img.shields.io/pypi/v/platform-agent.svg" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/platform-agent.svg" alt="Python">
  <img src="https://img.shields.io/github/license/openautonomyx/Platform-Agent.svg" alt="License">
</p>

> An autonomous AI agent platform powered by SurrealDB

## Features

- 🤖 **Autonomous Reasoning** - Agent can think and reason about tasks
- 💾 **Persistent Memory** - Remembers past interactions using SurrealDB
- 🔍 **Vector Search** - Semantic search for relevant context
- 🧠 **Knowledge Graph** - Structured reasoning with graphs
- 📝 **Tool Execution** - Can execute tools like file operations, bash commands
- 🔎 **Full-Text Search** - Search through documents and conversations

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

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `surrealdb_url` | SurrealDB WebSocket URL | `ws://localhost:8000/rpc` |
| `surrealdb_namespace` | Database namespace | `platform` |
| `surrealdb_database` | Database name | `agent` |
| `surrealdb_username` | Username | `root` |
| `surrealdb_password` | Password | `root` |
| `model` | LLM model | `gpt-4o-mini` |
| `temperature` | Sampling temperature | `0.7` |
| `max_tokens` | Max response tokens | `2048` |

## Architecture

```
┌─────────────────────────────────────┐
│         Platform Agent               │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  │
│  │   LLM      │  │   Memory    │  │
│  │ (OpenAI)   │  │ (SurrealDB) │  │
│  └─────────────┘  └──────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  │
│  │   Tools    │  │  Vector     │  │
│  │ (file,    │  │  Search     │  │
│  │  bash,    │  │            │  │
│  │  search)  │  │            │  │
│  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────┘
              │
              ▼
      ┌─────────────────┐
      │   SurrealDB     │
      │  (Backend)     │
      └─────────────────┘
```

## License

MIT License - see [LICENSE](LICENSE) for details.