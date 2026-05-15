"""Platform Agent Security - SurrealDB-native security features."""

import os
import secrets
from typing import Optional
from dataclasses import dataclass, field


# =============================================================================
# SurrealDB-Native Security
# =============================================================================

class SurrealDBSecurity:
    """Use SurrealDB's native security features:
    - DEFINE USER for authentication
    - DEFINE SCOPE for OAuth/sessions
    - PERMISSIONS for row-level security
    - DEFINE ACCESS for token management
    """
    
    @staticmethod
    async def setup_user(db, username: str, password: str, role: str = "viewer"):
        """Create user with SurrealDB.
        
        Uses: DEFINE USER $username ON DATABASE PASSWORD $password ROLE $role
        """
        await db.query(
            f"DEFINE USER {username} ON DATABASE PASSWORD '{password}' ROLE {role}"
        )
        return {"user": username, "role": role}
    
    @staticmethod
    async def setup_scope(
        db, 
        scope: str, 
        signup_query: str, 
        signin_query: str,
        session_duration: str = "24h",
    ):
        """Setup authentication scope.
        
        Uses: DEFINE SCOPE ... SIGNUP ... SIGNIN
        """
        await db.query(f"""
            DEFINE SCOPE {scope} SESSION {session_duration}
            SIGNUP ( {signup_query} )
            SIGNIN ( {signin_query} )
        """)
        return {"scope": scope}
    
    @staticmethod
    async def setup_permissions(
        db,
        table: str,
        select: str = "",
        create: str = "",
        update: str = "",
        delete: str = "",
    ):
        """Setup table permissions.
        
        Uses: DEFINE TABLE ... PERMISSIONS
        """
        perms = []
        if select:
            perms.append(f"FOR select WHERE {select}")
        if create:
            perms.append(f"FOR create WHERE {create}")
        if update:
            perms.append(f"FOR update WHERE {update}")
        if delete:
            perms.append(f"FOR delete WHERE {delete}")
        
        if perms:
            await db.query(f"""
                DEFINE TABLE {table} SCHEMALESS
                PERMISSIONS {' '.join(perms)}
            """)
        return {"table": table}


# =============================================================================
# Token Management (using SurrealDB)
# =============================================================================

class TokenManager:
    """Generate tokens - stored in SurrealDB for persistence."""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_session_id() -> str:
        return f"sess_{secrets.token_urlsafe(24)}"


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict = {}
    
    def is_allowed(self, key: str) -> bool:
        import time
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []
        
        self._requests[key] = [t for t in self._requests[key] if now - t < self.window]
        
        if len(self._requests[key]) >= self.max_requests:
            return False
        
        self._requests[key].append(now)
        return True