"""Platform Agent - An autonomous AI agent platform."""

__version__ = "0.1.0"
__author__ = "OpenAutonomyx"
__description__ = "An autonomous AI agent platform with SurrealDB backend"

from .agent import PlatformAgent
from .memory import AgentMemory
from .tools import Tool, FileTool, BashTool, SearchTool
from .config import AgentConfig

__all__ = [
    "PlatformAgent",
    "AgentMemory",
    "Tool",
    "FileTool", 
    "BashTool",
    "SearchTool",
    "AgentConfig",
]