"""Platform Agent - SurrealDB Models using native SurrealQL."""

from surrealdb import AsyncSurreal
import secrets
from .queries import *


# =============================================================================
# Member
# =============================================================================

class MemberDB:
    """Member using SurrealQL native functions."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, email: str, first_name: str, last_name: str, password: str) -> dict:
        return (await self.db.query(CREATE_MEMBER, {
            "email": email, "first_name": first_name, 
            "last_name": last_name, "password": password
        }))[0][0]
    
    async def get(self, email: str) -> dict:
        return (await self.db.query(
            "SELECT * FROM member WHERE email = $email LIMIT 1", {"email": email}
        ))[0][0]
    
    async def authenticate(self, email: str, password: str) -> dict:
        return (await self.db.query(AUTHENTICATE, {"email": email, "password": password}))[0]


# =============================================================================
# Invitation
# =============================================================================

class InvitationDB:
    """Invitation using SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, email: str, creator_id: str, resource_id: str, days: int = 7) -> dict:
        token = secrets.token_urlsafe(32)
        return (await self.db.query(CREATE_INVITATION, {
            "email": email, "creator": creator_id, "resource": resource_id,
            "invite_token": token, "days": days
        }))[0][0]
    
    async def accept(self, token: str, first_name: str, last_name: str, password: str) -> dict:
        return (await self.db.query(ACCEPT_INVITATION, {
            "token": token, "first_name": first_name, 
            "last_name": last_name, "password": password
        }))[0][0]
    
    async def list_pending(self, resource_id: str) -> list:
        return (await self.db.query(
            "SELECT * FROM invitation WHERE resource = $resource AND status = 'pending' ORDER BY created_at DESC",
            {"resource": resource_id}
        ))[0]
    
    async def revoke(self, token: str) -> bool:
        await self.db.query("DELETE FROM invitation WHERE invite_token = $token", {"token": token})


# =============================================================================
# Team
# =============================================================================

class TeamDB:
    """Team using SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, name: str, resource_id: str, icon: str = "👥") -> dict:
        return (await self.db.query(CREATE_TEAM, {
            "name": name, "resource": resource_id, "icon": icon
        }))[0][0]
    
    async def list(self, resource_id: str) -> list:
        return (await self.db.query(
            "SELECT * FROM team WHERE resource = $resource ORDER BY name",
            {"resource": resource_id}
        ))[0]
    
    async def add_member(self, team_id: str, member_id: str) -> dict:
        return (await self.db.query(ADD_TEAM_MEMBER, {
            "member": member_id, "team": team_id
        }))[0][0]


# =============================================================================
# Knowledge
# =============================================================================

class KnowledgeDB:
    """Knowledge using SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, title: str, content: str, resource_id: str, type: str = "doc", tags: list = None) -> dict:
        return (await self.db.query(
            """CREATE kn SET title = $title, content = $content, type = $type, 
                tags = $tags, resource = $resource, created_at = time::now()""",
            {"title": title, "content": content, "type": type, 
             "tags": tags or [], "resource": resource_id}
        ))[0][0]
    
    async def search(self, query: str, resource_id: str, limit: int = 5) -> list:
        return (await self.db.query(SEARCH_KNOWLEDGE, {
            "query": query, "resource": resource_id, "limit": limit
        }))[0]
    
    async def list(self, resource_id: str, type: str = None) -> list:
        q = "SELECT * FROM kn WHERE resource = $resource ORDER BY created_at DESC"
        if type:
            q += f" AND type = '{type}'"
        return (await self.db.query(q, {"resource": resource_id}))[0]


# =============================================================================
# Conversation
# =============================================================================

class ConversationDB:
    """Conversation using SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, title: str, member_id: str, resource_id: str) -> dict:
        return (await self.db.query(CREATE_CONVERSATION, {
            "title": title, "member": member_id, "resource": resource_id
        }))[0][0]
    
    async def add_message(self, conv_id: str, role: str, content: str) -> dict:
        return (await self.db.query(ADD_MESSAGE, {
            "conv_id": conv_id, "role": role, "content": content
        }))[0][0]
    
    async def get_with_messages(self, conv_id: str) -> dict:
        return (await self.db.query(GET_CONVERSATION, {"conv_id": conv_id}))[0][0]
    
    async def list(self, resource_id: str) -> list:
        return (await self.db.query(
            "SELECT * FROM conv WHERE resource = $resource ORDER BY updated_at DESC",
            {"resource": resource_id}
        ))[0]


# =============================================================================
# Tool
# =============================================================================

class ToolDB:
    """Tool using SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, name: str, description: str, action: str, resource_id: str, schema: dict = None) -> dict:
        return (await self.db.query(CREATE_TOOL, {
            "name": name, "description": description, "action": action,
            "schema": schema or {}, "resource": resource_id
        }))[0][0]
    
    async def list(self, resource_id: str) -> list:
        return (await self.db.query(
            "SELECT * FROM tool WHERE resource = $resource AND enabled = true",
            {"resource": resource_id}
        ))[0]


# =============================================================================
# Analytics
# =============================================================================

class AnalyticsDB:
    """Analytics using SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def track(self, event: str, member_id: str, resource_id: str, properties: dict = None) -> dict:
        return (await self.db.query(TRACK_EVENT, {
            "event": event, "member": member_id, "resource": resource_id,
            "properties": properties or {}
        }))[0][0]
    
    async def get_stats(self, resource_id: str) -> dict:
        return (await self.db.query(GET_STATS, {"resource": resource_id}))[0][0]