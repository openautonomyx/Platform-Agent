"""Platform Agent Skills - Extension capabilities."""

from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class Skill(ABC):
    """Base class for agent skills."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Skill name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Skill description."""
        pass
    
    @property
    def parameters(self) -> dict[str, Any]:
        """Skill parameters schema."""
        return {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the skill."""
        pass


# -----------------------------------------------------------------------------
# Built-in Skills
# -----------------------------------------------------------------------------

@dataclass
class FileReadSkill(Skill):
    """Read file contents."""
    
    @property
    def name(self) -> str:
        return "file_read"
    
    @property
    def description(self) -> str:
        return "Read contents of a file"
    
    async def execute(self, path: str = "", **kwargs) -> str:
        """Read file."""
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error: {e}"


@dataclass
class FileWriteSkill(Skill):
    """Write file contents."""
    
    @property
    def name(self) -> str:
        return "file_write"
    
    @property
    def description(self) -> str:
        return "Write contents to a file"
    
    async def execute(self, path: str = "", content: str = "", **kwargs) -> str:
        """Write file."""
        try:
            with open(path, "w") as f:
                f.write(content)
            return f"Written to {path}"
        except Exception as e:
            return f"Error: {e}"


@dataclass
class BashSkill(Skill):
    """Execute bash command."""
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return "Execute a bash command"
    
    async def execute(self, command: str = "", **kwargs) -> str:
        """Run command."""
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout or result.stderr or "Done"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {e}"


@dataclass
class SearchWebSkill(Skill):
    """Web search."""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    async def execute(self, query: str = "", limit: int = 5, **kwargs) -> str:
        """Search web."""
        # Placeholder - integrate with search API
        return f"Search results for '{query}' (search API not configured)"


@dataclass
class FetchWebSkill(Skill):
    """Fetch web page."""
    
    @property
    def name(self) -> str:
        return "web_fetch"
    
    @property
    def description(self) -> str:
        return "Fetch content from a URL"
    
    async def execute(self, url: str = "", **kwargs) -> str:
        """Fetch URL."""
        # Placeholder - integrate with HTTP client
        return f"Fetched {url} (HTTP client not configured)"


# -----------------------------------------------------------------------------
# Skill Registry
# -----------------------------------------------------------------------------

class SkillRegistry:
    """Registry for agent skills."""
    
    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default skills."""
        defaults = [
            FileReadSkill(),
            FileWriteSkill(),
            BashSkill(),
            SearchWebSkill(),
            FetchWebSkill(),
        ]
        for skill in defaults:
            self.register(skill)
    
    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill
    
    def unregister(self, name: str) -> None:
        """Unregister a skill."""
        self._skills.pop(name, None)
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill."""
        return self._skills.get(name)
    
    def list(self) -> list[dict[str, str]]:
        """List all skills."""
        return [
            {"name": s.name, "description": s.description}
            for s in self._skills.values()
        ]
    
    async def execute(self, name: str, **kwargs) -> Any:
        """Execute a skill."""
        skill = self._skills.get(name)
        if not skill:
            return f"Error: Skill not found: {name}"
        return await skill.execute(**kwargs)


# Default registry instance
_default_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """Get the default skill registry."""
    return _default_registry