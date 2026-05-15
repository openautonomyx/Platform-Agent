"""Platform Agent Security - Best practices and security utilities."""

import os
import secrets
from typing import Optional
from dataclasses import dataclass, field


# =============================================================================
# Security Configuration
# =============================================================================

@dataclass
class SecurityConfig:
    """Security configuration for Platform Agent."""
    
    # Authentication
    require_auth: bool = field(default_factory=lambda: os.getenv("REQUIRE_AUTH", "false").lower() == "true")
    session_timeout: int = field(default_factory=lambda: int(os.getenv("SESSION_TIMEOUT", "3600")))
    max_login_attempts: int = 5
    
    # Encryption
    encrypt_sensitive: bool = field(default_factory=lambda: os.getenv("ENCRYPT_SENSITIVE", "true").lower() == "true")
    
    # Rate limiting
    rate_limit_enabled: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT", "false").lower() == "true")
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # API keys
    require_api_key: bool = field(default_factory=lambda: os.getenv("REQUIRE_API_KEY", "false").lower() == "true")
    allowed_api_keys: list = field(default_factory=list)


# =============================================================================
# Input Validation & Sanitization
# =============================================================================

class InputValidator:
    """Validate and sanitize user inputs."""
    
    @staticmethod
    def sanitize_query(query: str, max_length: int = 10000) -> str:
        """Sanitize a query string."""
        if not query:
            return ""
        
        # Strip whitespace
        query = query.strip()
        
        # Truncate
        if len(query) > max_length:
            query = query[:max_length]
        
        return query
    
    @staticmethod
    def validate_api_key(api_key: str, valid_keys: list) -> bool:
        """Validate API key."""
        if not valid_keys:
            return True
        return api_key in valid_keys
    
    @staticmethod
    def is_safe_input(text: str) -> bool:
        """Check if input is safe (no obvious injection)."""
        # Basic checks - extend as needed
        dangerous = ["<script", "javascript:", "onerror=", "onclick="]
        lower = text.lower()
        return not any(d in lower for d in dangerous)


# =============================================================================
# Token Management
# =============================================================================

class TokenManager:
    """Generate and validate tokens."""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a session ID."""
        return f"sess_{secrets.token_urlsafe(24)}"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password (placeholder - use bcrypt in production)."""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


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
        """Check if request is allowed."""
        import time
        
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []
        
        # Remove old requests
        self._requests[key] = [
            t for t in self._requests[key]
            if now - t < self.window
        ]
        
        # Check limit
        if len(self._requests[key]) >= self.max_requests:
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True


# =============================================================================
# Audit Logging
# =============================================================================

class AuditLogger:
    """Log security events."""
    
    def __init__(self):
        self._log_file = "security_audit.log"
    
    def log(self, event_type: str, details: dict):
        """Log a security event."""
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **details,
        }
        
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    def log_login(self, user: str, success: bool, ip: str = ""):
        self.log("login", {"user": user, "success": success, "ip": ip})
    
    def log_access_denied(self, user: str, resource: str):
        self.log("access_denied", {"user": user, "resource": resource})
    
    def log_rate_limit(self, ip: str):
        self.log("rate_limit", {"ip": ip})


# Default instances
_default_audit = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get audit logger."""
    return _default_audit