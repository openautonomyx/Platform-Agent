"""Platform Agent Tools - extensibility capabilities."""

import os
import subprocess
import json
import asyncio
import aiohttp
from typing import Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Tool(ABC):
    """Base class for agent tools.
    
    Tools extend the agent's capabilities by providing specific actions.
    Each tool has a name, description, and async execute method.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    def schema(self) -> dict[str, Any]:
        """JSON schema for the tool."""
        return {
            "name": self.name,
            "description": self.description,
        }
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        pass


# -----------------------------------------------------------------------------
# File Tools
# -----------------------------------------------------------------------------

@dataclass
class FileTool(Tool):
    """Tool for file operations."""
    
    @property
    def name(self) -> str:
        return "file"
    
    @property
    def description(self) -> str:
        return "Read, write, and manage files"
    
    async def execute(self, operation: str = "read", path: str = "", content: str = "") -> str:
        """Execute file operation."""
        if operation == "read":
            try:
                with open(path, "r") as f:
                    return f.read()
            except FileNotFoundError:
                return f"File not found: {path}"
            except Exception as e:
                return f"Error reading file: {e}"
        
        elif operation == "write":
            try:
                with open(path, "w") as f:
                    f.write(content)
                return f"Written to {path}"
            except Exception as e:
                return f"Error writing file: {e}"
        
        elif operation == "exists":
            return str(os.path.exists(path))
        
        return f"Unknown operation: {operation}"


# -----------------------------------------------------------------------------
# Shell Tools
# -----------------------------------------------------------------------------

@dataclass
class BashTool(Tool):
    """Tool for running bash commands."""
    
    timeout: int = 30
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return "Execute bash commands"
    
    async def execute(self, command: str = "", cwd: Optional[str] = None) -> str:
        """Execute bash command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            output = result.stdout or result.stderr or ""
            if result.returncode != 0:
                return f"Error (exit {result.returncode}): {output}"
            return output or "Command executed successfully"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error: {e}"


# -----------------------------------------------------------------------------
# Web Tools
# -----------------------------------------------------------------------------

@dataclass
class SearchTool(Tool):
    """Tool for web search."""
    
    api_key: Optional[str] = field(default=None)
    
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    async def execute(self, query: str = "", limit: int = 5) -> str:
        """Execute web search."""
        # Use Tavily API if configured
        if self.api_key:
            return await self._search_tavily(query, limit)
        return f"Search results for '{query}' (search API not configured - set TAVILY_API_KEY)"


@dataclass 
class WebFetchTool(Tool):
    """Tool for fetching web pages."""
    
    @property
    def name(self) -> str:
        return "fetch"
    
    @property
    def description(self) -> str:
        return "Fetch content from URLs"
    
    async def execute(self, url: str = "") -> str:
        """Fetch a URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()
        except Exception as e:
            return f"Error fetching {url}: {e}"


# -----------------------------------------------------------------------------
# Utility Tools
# -----------------------------------------------------------------------------

@dataclass
class CalculatorTool(Tool):
    """Tool for calculations."""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform calculations (basic math)"
    
    async def execute(self, expression: str = "") -> str:
        """Evaluate expression."""
        try:
            # Safe eval for basic math
            allowed = {"__builtins__": {}, "abs": abs, "max": max, "min": min, "round": round}
            result = eval(expression, allowed)
            return str(result)
        except Exception as e:
            return f"Error: {e}"


@dataclass
class JSONTool(Tool):
    """Tool for JSON operations."""
    
    @property
    def name(self) -> str:
        return "json"
    
    @property
    def description(self) -> str:
        return "Parse and Format JSON"
    
    async def execute(self, operation: str = "parse", content: str = "") -> str:
        """Execute JSON operation."""
        if operation == "parse":
            try:
                return json.dumps(json.loads(content))
            except Exception as e:
                return f"Error: {e}"
        elif operation == "format":
            try:
                return json.dumps(json.loads(content), indent=2)
            except Exception as e:
                return f"Error: {e}"
        return f"Unknown operation: {operation}"


# -----------------------------------------------------------------------------
# Tool Registry
# -----------------------------------------------------------------------------

class ToolRegistry:
    """Registry for agent tools."""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default tools."""
        defaults = [
            FileTool(),
            BashTool(),
            SearchTool(),
            WebFetchTool(),
            CalculatorTool(),
            JSONTool(),
        ]
        for tool in defaults:
            self.register(tool)
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        self._tools.pop(name, None)
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool."""
        return self._tools.get(name)
    
    def list(self) -> list[dict[str, str]]:
        """List all tools."""
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool."""
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool not found: {name}"
        return await tool.execute(**kwargs)


# Default registry
_default_registry = ToolRegistry()


def get_tools() -> ToolRegistry:
    """Get the default tool registry."""
    return _default_registry