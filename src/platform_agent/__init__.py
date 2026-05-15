"""Platform Agent - An autonomous AI agent platform."""

__version__ = "0.1.0"
__author__ = "OpenAutonomyx"
__description__ = "An autonomous AI agent platform with SurrealDB backend"

from .agent import PlatformAgent, SyncPlatformAgent, create_agent
from .memory import AgentMemory
from .config import AgentConfig
from .tools import Tool, FileTool, BashTool, SearchTool
from .skills import Skill, SkillRegistry, get_registry

__all__ = [
    # Core
    "PlatformAgent",
    "SyncPlatformAgent", 
    "create_agent",
    # Memory
    "AgentMemory",
    # Config
    "AgentConfig",
    # Tools
    "Tool",
    "FileTool",
    "BashTool",
    "SearchTool",
    # Skills
    "Skill",
    "SkillRegistry",
    "get_registry",
]