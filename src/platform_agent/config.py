"""Platform Agent configuration."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for Platform Agent."""
    
    # SurrealDB connection
    surrealdb_url: str = "ws://localhost:8000/rpc"
    surrealdb_namespace: str = "platform"
    surrealdb_database: str = "agent"
    surrealdb_username: str = "root"
    surrealdb_password: str = "root"
    
    # LLM settings
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048
    
    # Memory settings
    memory_limit: int = 100
    vector_search_limit: int = 5
    
    # Agent settings
    max_iterations: int = 10
    verbose: bool = False
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config from environment variables."""
        import os
        return cls(
            surrealdb_url=os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc"),
            surrealdb_namespace=os.getenv("SURREALDB_NAMESPACE", "platform"),
            surrealdb_database=os.getenv("SURREALDB_DATABASE", "agent"),
            surrealdb_username=os.getenv("SURREALDB_USERNAME", "root"),
            surrealdb_password=os.getenv("SURREALDB_PASSWORD", "root"),
        )