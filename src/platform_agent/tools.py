"""Platform Agent tools."""

import os
import subprocess
from typing import Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Tool(ABC):
    """Base class for agent tools."""
    
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
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        pass


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
    
    async def read(self, path: str) -> str:
        """Read a file."""
        return await self.execute(operation="read", path=path)
    
    async def write(self, path: str, content: str) -> str:
        """Write to a file."""
        return await self.execute(operation="write", path=path, content=content)


@dataclass
class BashTool(Tool):
    """Tool for running bash commands."""
    
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
                timeout=30,
            )
            output = result.stdout or result.stderr or ""
            if result.returncode != 0:
                return f"Error (exit {result.returncode}): {output}"
            return output or "Command executed successfully"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error: {e}"
    
    async def run(self, command: str, cwd: Optional[str] = None) -> str:
        """Run a command."""
        return await self.execute(command=command, cwd=cwd)


@dataclass
class SearchTool(Tool):
    """Tool for web search."""
    
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    async def execute(self, query: str = "", limit: int = 5) -> str:
        """Execute web search."""
        # Placeholder - in production, integrate with search API
        return f"Search results for '{query}' (placeholder)"
    
    async def search(self, query: str, limit: int = 5) -> str:
        """Search the web."""
        return await self.execute(query=query, limit=limit)


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
        # Placeholder - in production, use requests/aiohttp
        return f"Fetched {url} (placeholder)"
    
    async def fetch(self, url: str) -> str:
        """Fetch a URL."""
        return await self.execute(url=url)