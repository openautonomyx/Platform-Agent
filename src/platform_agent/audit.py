"""Platform Agent - Audit Logging (Native SurrealQL)."""

from surrealdb import AsyncSurreal


# =============================================================================
# Schema - Native SurrealQL
# =============================================================================

SCHEMA = """
DEFINE TABLE audit SCHEMAFULL;
DEFINE FIELD action ON audit TYPE string;
DEFINE FIELD actor ON audit TYPE record(member);
DEFINE FIELD resource ON audit TYPE record;
DEFINE FIELD details ON audit TYPE object DEFAULT {};
DEFINE FIELD ip ON audit TYPE option<string>;
DEFINE FIELD created_at ON audit TYPE datetime;
DEFINE FIELD replayed_at ON audit TYPE option<datetime>;
DEFINE INDEX action_idx ON audit FIELDS action;
DEFINE INDEX actor_idx ON audit FIELDS actor;
DEFINE INDEX created_idx ON audit FIELDS created_at;
"""


# =============================================================================
# Native SurrealQL Queries
# =============================================================================

LOG_ACTION = """
CREATE audit SET
    action = $action,
    actor = $actor,
    resource = $resource,
    details = $details,
    ip = $ip,
    created_at = time::now()
"""

LIST_AUDIT = """
SELECT * FROM audit WHERE action = $action ORDER BY created_at DESC LIMIT $limit
"""

LIST_BY_MEMBER = """
SELECT * FROM audit WHERE actor = $actor ORDER BY created_at DESC LIMIT $limit
"""

REPLAY_ENTRY = """
UPDATE audit SET replayed_at = time::now() WHERE id = $audit_id
"""


# =============================================================================
# Audit Actions
# =============================================================================

class Audit:
    SIGN_IN = "auth:signin"
    SIGN_UP = "auth:signup"
    SIGN_OUT = "auth:signout"
    MEMBER_CREATE = "member:create"
    INVITE_CREATE = "invite:create"
    INVITE_ACCEPT = "invite:accept"
    ORG_CREATE = "org:create"
    MEMBER_ADD = "member:add"
    TEAM_CREATE = "team:create"
    DOC_CREATE = "doc:create"
    DOC_DELETE = "doc:delete"
    MESSAGE_SEND = "message:send"
    TOOL_EXECUTE = "tool:execute"
    SETTINGS_UPDATE = "settings:update"


# =============================================================================
# Audit Logger - Native SurrealQL
# =============================================================================

class AuditLogger:
    """Audit logging using native SurrealQL."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def log(
        self,
        action: str,
        actor_id: str = None,
        resource_id: str = None,
        details: dict = None,
        ip: str = None,
    ):
        """Log audit event - native SurrealQL."""
        await self.db.query(
            LOG_ACTION,
            {
                "action": action,
                "actor": actor_id,
                "resource": resource_id,
                "details": details or {},
                "ip": ip,
            }
        )
    
    async def list(
        self,
        action: str = None,
        actor_id: str = None,
        limit: int = 50,
    ):
        """List logs - native SurrealQL."""
        cond = "action = $action" if action else "actor = $actor"
        params = {"action": action, "actor": actor_id, "limit": limit}
        
        result = await self.db.query(
            f"SELECT * FROM audit WHERE {cond} ORDER BY created_at DESC LIMIT $limit",
            params
        )
        return result[0] if result[0] else []
    
    async def replay(self, audit_id: str):
        """Mark as replayed - native SurrealQL."""
        await self.db.query(REPLAY_ENTRY, {"audit_id": audit_id})
    
    # Helpers
    async def sign_in(self, email: str, success: bool = True, ip: str = None):
        action = Audit.SIGN_IN if success else "auth:signin:fail"
        await self.log(action, details={"email": email}, ip=ip)
    
    async def sign_up(self, email: str, member_id: str):
        await self.log(Audit.SIGN_UP, actor_id=member_id, details={"email": email})
    
    async def create_invite(self, email: str, creator_id: str, resource_id: str):
        await self.log(
            Audit.INVITE_CREATE,
            actor_id=creator_id,
            resource_id=resource_id,
            details={"email": email},
        )
    
    async def create_team(self, name: str, creator_id: str, resource_id: str):
        await self.log(
            Audit.TEAM_CREATE,
            actor_id=creator_id,
            resource_id=resource_id,
            details={"name": name},
        )
    
    async def send_message(self, member_id: str, conv_id: str, preview: str):
        await self.log(
            Audit.MESSAGE_SEND,
            actor_id=member_id,
            resource_id=conv_id,
            details={"preview": preview[:50]},
        )