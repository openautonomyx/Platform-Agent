"""Platform Agent - SurrealDB Invitation System."""

import os
import secrets
from datetime import datetime, timedelta
from surrealdb import AsyncSurreal


# =============================================================================
# Invitation Model
# =============================================================================

class InvitationDB:
    """Invitation database operations."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, email: str, creator_id: str, resource_id: str, days: int = 7) -> dict:
        """Create invitation."""
        # Check if member exists
        existing = await self.db.query(
            "SELECT VALUE id FROM member WHERE email = $email LIMIT 1",
            {"email": email}
        )
        if existing[0]:
            raise ValueError("MEMBER_ALREADY_EXISTS")
        
        # Create invitation
        invite_token = secrets.token_urlsafe(32)
        invitation = await self.db.query(
            """CREATE invitation SET
                creator = $creator_id,
                email = $email,
                invite_token = $invite_token,
                resource = $resource_id,
                expires_at = time::now() + duration::from_days($days),
                status = 'pending'
            """,
            {
                "creator_id": creator_id,
                "email": email,
                "invite_token": invite_token,
                "resource_id": resource_id,
                "days": days
            }
        )
        return invitation[0]
    
    async def accept(self, invite_token: str, first_name: str, last_name: str, password: str) -> dict:
        """Accept invitation and create member."""
        # Get invitation
        inv = await self.db.query(
            "SELECT * FROM invitation WHERE invite_token = $token AND status = 'pending' LIMIT 1",
            {"token": invite_token}
        )
        if not inv[0]:
            raise ValueError("INVITATION_NOT_FOUND")
        
        inv_row = inv[0][0]
        
        # Check expiration
        expires = inv_row.get("expires_at")
        if expires and datetime.fromisoformat(expires.replace("Z", "+00:00")) < datetime.now():
            raise ValueError("INVITATION_EXPIRED")
        
        # Create or get member
        existing = await self.db.query(
            "SELECT VALUE id FROM member WHERE email = $email LIMIT 1",
            {"email": inv_row["email"]}
        )
        
        if existing[0]:
            member_id = existing[0]
        else:
            # Create member
            member = await self.db.query(
                """CREATE member SET
                    email = $email,
                    first_name = $first_name,
                    last_name = $last_name,
                    password = crypto::argon2::generate($password),
                    created_at = time::now(),
                    created_by = $creator
                """,
                {
                    "email": inv_row["email"],
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": password,
                    "creator": inv_row["creator"]
                }
            )
            member_id = member[0]["id"]
        
        # Create membership
        existing_membership = await self.db.query(
            "SELECT VALUE id FROM membership WHERE in = $member AND out = $resource LIMIT 1",
            {"member": member_id, "resource": inv_row["resource"]}
        )
        
        if not existing_membership[0]:
            await self.db.query(
                "RELATE $member->membership->$resource",
                {"member": member_id, "resource": inv_row["resource"]}
            )
        
        # Mark invitation used
        await self.db.query(
            "UPDATE invitation SET status = 'used', used_at = time::now() WHERE invite_token = $token",
            {"token": invite_token}
        )
        
        return {"member_id": member_id, "email": inv_row["email"]}
    
    async def get(self, token: str) -> dict:
        """Get invitation by token."""
        inv = await self.db.query(
            "SELECT * FROM invitation WHERE invite_token = $token LIMIT 1",
            {"token": token}
        )
        return inv[0][0] if inv[0] else None
    
    async def list_pending(self, resource_id: str) -> list:
        """List pending invitations for resource."""
        invs = await self.db.query(
            "SELECT * FROM invitation WHERE resource = $resource AND status = 'pending' ORDER BY created_at DESC",
            {"resource": resource_id}
        )
        return inv[0] if inv[0] else []
    
    async def revoke(self, token: str) -> bool:
        """Revoke invitation."""
        result = await self.db.query(
            "DELETE FROM invitation WHERE invite_token = $token",
            {"token": token}
        )
        return True


# =============================================================================
# Member Model  
# =============================================================================

class MemberDB:
    """Member database operations."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, email: str, first_name: str, last_name: str, password: str) -> dict:
        """Create member."""
        member = await self.db.query(
            """CREATE member SET
                email = $email,
                first_name = $first_name,
                last_name = $last_name,
                password = crypto::argon2::generate($password),
                created_at = time::now()
            """,
            {"email": email, "first_name": first_name, "last_name": last_name, "password": password}
        )
        return member[0]
    
    async def get(self, email: str) -> dict:
        """Get member by email."""
        m = await self.db.query(
            "SELECT * FROM member WHERE email = $email LIMIT 1",
            {"email": email}
        )
        return m[0][0] if m[0] else None
    
    async def verify_password(self, email: str, password: str) -> dict:
        """Verify password."""
        member = await self.get(email)
        if not member:
            return None
        
        # Verify hash
        verified = await self.db.query(
            "RETURN crypto::argon2::verify($hash, $password)",
            {"hash": member["password"], "password": password}
        )
        
        return member if verified[0] else None
    
    async def authenticate(self, email: str, password: str) -> dict:
        """Authenticate member."""
        return await self.verify_password(email, password)


# =============================================================================
# Team Model
# =============================================================================

class TeamDB:
    """Team database operations."""
    
    def __init__(self, db: AsyncSurreal):
        self.db = db
    
    async def create(self, name: str, resource_id: str, icon: str = "👥") -> dict:
        """Create team."""
        team = await self.db.query(
            """CREATE team SET
                name = $name,
                icon = $icon,
                resource = $resource,
                created_at = time::now()
            """,
            {"name": name, "icon": icon, "resource": resource_id}
        )
        return team[0]
    
    async def list(self, resource_id: str) -> list:
        """List teams for resource."""
        teams = await self.db.query(
            "SELECT * FROM team WHERE resource = $resource ORDER BY name",
            {"resource": resource_id}
        )
        return teams[0] if teams[0] else []
    
    async def add_member(self, team_id: str, member_id: str) -> dict:
        """Add member to team."""
        return await self.db.query(
            "RELATE $member->team_member->$team",
            {"member": member_id, "team": team_id}
        )