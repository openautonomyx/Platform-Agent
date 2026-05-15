"""Platform Agent - An autonomous AI agent platform."""

__version__ = "0.1.0"
__author__ = "OpenAutonomyx"
__description__ = "An autonomous AI agent platform with SurrealDB backend"

from .agent import PlatformAgent, SurrealMemory, SurrealEmbeddings, SyncPlatformAgent, create_agent
from .config import AgentConfig, DEFAULT_SYSTEM_PROMPT, DEFAULT_WELCOME_MESSAGE
from .tools import Tool, FileTool, BashTool, SearchTool, ToolRegistry
from .skills import Skill, SkillRegistry, get_registry

__all__ = [
    # Core
    "PlatformAgent",
    "SurrealMemory", 
    "SurrealEmbeddings",
    "SyncPlatformAgent", 
    "create_agent",
    # Config
    "AgentConfig",
    "DEFAULT_SYSTEM_PROMPT",
    "DEFAULT_WELCOME_MESSAGE",
    # Tools
    "Tool",
    "FileTool",
    "BashTool",
    "SearchTool",
    "ToolRegistry",
    # Skills
    "Skill",
    "SkillRegistry",
    "get_registry",
]