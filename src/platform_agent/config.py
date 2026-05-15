"""Platform Agent configuration."""

import os
from dataclasses import dataclass, field
from typing import Optional


def _get_env(key: str, default: str = "") -> str:
    """Get environment variable."""
    return os.getenv(key, default)


DEFAULT_SYSTEM_PROMPT = """You are Platform Agent, an autonomous AI agent with persistent memory and tool execution capabilities.

Core Capabilities:
- Memory: Remember past interactions using SurrealDB
- Tools: file, bash, search, fetch, calculator, json
- Reasoning: Step-by-step problem solving

Guidelines:
- Be helpful, honest, and concise
- Use tools when they would be useful
- Ask for clarification when needed
- Admit when you don't know something"""


DEFAULT_WELCOME_MESSAGE = "Hi! I'm Platform Agent. I have persistent memory and various tools to help you. How can I assist you today?"


DEFAULT_ERROR_MESSAGE = "Sorry, something went wrong. Let me try again or suggest an alternative."


# Placeholder response when LLM is not configured
PLACEHOLDER_RESPONSE = """This is a placeholder response.

To enable full AI capabilities, configure:
1. Set LLM_API_KEY in .env
2. Or pass llm_api_key to AgentConfig

Currently running in demo mode."""


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
    llm_provider: str = field(default_factory=lambda: _get_env("LLM_PROVIDER", "ollama"))
    model: str = field(default_factory=lambda: _get_env("LLM_MODEL", ""))
    llm_api_key: str = field(default_factory=lambda: _get_env("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: _get_env("LLM_BASE_URL", ""))
    temperature: float = field(default_factory=lambda: float(_get_env("LLM_TEMPERATURE", "0.7")))
    max_tokens: int = field(default_factory=lambda: int(_get_env("LLM_MAX_TOKENS", "2048")))
    
    # Prompts (customizable)
    system_prompt: str = field(default_factory=lambda: _get_env("AGENT_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT))
    welcome_message: str = field(default_factory=lambda: _get_env("AGENT_WELCOME_MESSAGE", DEFAULT_WELCOME_MESSAGE))
    error_message: str = field(default_factory=lambda: _get_env("AGENT_ERROR_MESSAGE", DEFAULT_ERROR_MESSAGE))
    
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