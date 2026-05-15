"""Platform Agent configuration."""

import os
from dataclasses import dataclass, field
from typing import Optional


def _get_env(key: str, default: str = "") -> str:
    """Get environment variable."""
    return os.getenv(key, default)


@dataclass
class AgentConfig:
    """Configuration for Platform Agent."""
    
    # SurrealDB connection
    surrealdb_url: str = field(default_factory=lambda: _get_env("SURREALDB_URL", "ws://localhost:8000/rpc"))
    surrealdb_namespace: str = field(default_factory=lambda: _get_env("SURREALDB_NAMESPACE", "platform"))
    surrealdb_database: str = field(default_factory=lambda: _get_env("SURREALDB_DATABASE", "agent"))
    surrealdb_username: str = field(default_factory=lambda: _get_env("SURREALDB_USERNAME", "root"))
    surrealdb_password: str = field(default_factory=lambda: _get_env("SURREALDB_PASSWORD", "root"))
    
    # LLM settings
    model: str = field(default_factory=lambda: _get_env("LLM_MODEL", "gpt-4o-mini"))
    llm_api_key: str = field(default_factory=lambda: _get_env("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: _get_env("LLM_BASE_URL", ""))
    temperature: float = field(default_factory=lambda: float(_get_env("LLM_TEMPERATURE", "0.7")))
    max_tokens: int = field(default_factory=lambda: int(_get_env("LLM_MAX_TOKENS", "2048")))
    
    # Memory settings
    memory_limit: int = field(default_factory=lambda: int(_get_env("AGENT_MEMORY_LIMIT", "100")))
    vector_search_limit: int = field(default_factory=lambda: int(_get_env("AGENT_VECTOR_SEARCH_LIMIT", "5")))
    
    # Agent settings
    max_iterations: int = field(default_factory=lambda: int(_get_env("AGENT_MAX_ITERATIONS", "10")))
    verbose: bool = field(default_factory=lambda: _get_env("AGENT_VERBOSE", "false").lower() == "true")
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config entirely from environment variables."""
        return cls()