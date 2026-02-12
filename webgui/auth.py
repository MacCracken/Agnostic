"""
Authentication and Authorization Module
JWT-based multi-provider authentication with role-based access control.
"""
import os
import sys
import json
import asyncio
import jwt
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
import secrets
from pathlib import Path

# Add config path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.environment import config

logger = logging.getLogger(__name__)

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    TEAM_LEAD = "team_lead"
    QA_ENGINEER = "qa_engineer"
    VIEWER = "viewer"
    API_USER = "api_user"

class Permission(Enum):
    SESSIONS_READ = "sessions:read"
    SESSIONS_WRITE = "sessions:write"
    SESSIONS_DELETE = "sessions:delete"
    AGENTS_CONTROL = "agents:control"
    REPORTS_GENERATE = "reports:generate"
    REPORTS_EXPORT = "reports:export"
    USERS_MANAGE = "users:manage"
    SYSTEM_CONFIGURE = "system:configure"
    API_ACCESS = "api:access"

class AuthProvider(Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    AZURE_AD = "azure_ad"
    SAML = "saml"

@dataclass
class User:
    user_id: str
    email: str
    name: str
    role: UserRole
    auth_provider: AuthProvider
    organization_id: Optional[str]
    team_id: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    permissions: Set[Permission]
    metadata: Dict[str, Any]

@dataclass
class AuthToken:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    scope: str = "read write"

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self):
        self.redis_client = config.get_redis_client()
        self.secret_key = os.getenv("WEBGUI_SECRET_KEY", secrets.token_urlsafe(32))
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7
        
        # Role permissions mapping
        self.role_permissions = {
            UserRole.SUPER_ADMIN: {
                Permission.SESSIONS_READ, Permission.SESSIONS_WRITE, Permission.SESSIONS_DELETE,
                Permission.AGENTS_CONTROL, Permission.REPORTS_GENERATE, Permission.REPORTS_EXPORT,
                Permission.USERS_MANAGE, Permission.SYSTEM_CONFIGURE, Permission.API_ACCESS
            },
            UserRole.ORG_ADMIN: {
                Permission.SESSIONS_READ, Permission.SESSIONS_WRITE, Permission.SESSIONS_DELETE,
                Permission.AGENTS_CONTROL, Permission.REPORTS_GENERATE, Permission.REPORTS_EXPORT,
                Permission.USERS_MANAGE, Permission.API_ACCESS
            },
            UserRole.TEAM_LEAD: {
                Permission.SESSIONS_READ, Permission.SESSIONS_WRITE,
                Permission.AGENTS_CONTROL, Permission.REPORTS_GENERATE, Permission.REPORTS_EXPORT
            },
            UserRole.QA_ENGINEER: {
                Permission.SESSIONS_READ, Permission.SESSIONS_WRITE,
                Permission.AGENTS_CONTROL, Permission.REPORTS_GENERATE
            },
            UserRole.VIEWER: {
                Permission.SESSIONS_READ, Permission.REPORTS_GENERATE
            },
            UserRole.API_USER: {
                Permission.SESSIONS_READ, Permission.SESSIONS_WRITE, Permission.API_ACCESS
            }
        }
    
    async def authenticate_user(
        self,
        email: str,
        password: Optional[str] = None,
        provider: AuthProvider = AuthProvider.LOCAL,
        auth_code: Optional[str] = None,
        id_token: Optional[str] = None
    ) -> Optional[User]:
        """Authenticate user with various providers"""
        try:
            if provider == AuthProvider.LOCAL:
                return await self._authenticate_local(email, password or "")
            elif provider == AuthProvider.GOOGLE:
                return await self._authenticate_google(auth_code, id_token)
            elif provider == AuthProvider.GITHUB:
                return await self._authenticate_github(auth_code)
            elif provider == AuthProvider.AZURE_AD:
                return await self._authenticate_azure_ad(auth_code, id_token)
            else:
                logger.error(f"Unsupported auth provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    async def _authenticate_local(self, email: str, password: str) -> Optional[User]:
        """Local authentication with password"""
        try:
            # Get user from Redis
            user_key = f"user:email:{email}"
            user_data = self.redis_client.get(user_key)
            
            if not user_data:
                return None
            
            user_dict = json.loads(user_data)
            
            # Verify password
            password_hash = user_dict.get("password_hash")
            if not password_hash or not self._verify_password(password, password_hash):
                return None
            
            # Create User object
            user = User(
                user_id=user_dict["user_id"],
                email=user_dict["email"],
                name=user_dict["name"],
                role=UserRole(user_dict["role"]),
                auth_provider=AuthProvider.LOCAL,
                organization_id=user_dict.get("organization_id"),
                team_id=user_dict.get("team_id"),
                created_at=datetime.fromisoformat(user_dict["created_at"]),
                last_login=datetime.fromisoformat(user_dict["last_login"]) if user_dict.get("last_login") else None,
                is_active=user_dict.get("is_active", True),
                permissions=self.role_permissions.get(UserRole(user_dict["role"]), set()),
                metadata=user_dict.get("metadata", {})
            )
            
            # Update last login
            await self._update_last_login(user.user_id)
            
            return user
            
        except Exception as e:
            logger.error(f"Local authentication error: {e}")
            return None
    
    async def _authenticate_google(self, auth_code: Optional[str], id_token: Optional[str]) -> Optional[User]:
        """Google OAuth2 authentication"""
        try:
            # For now, placeholder implementation
            # In production, would verify ID token with Google's public keys
            
            if id_token:
                # Decode and verify ID token
                payload = jwt.decode(id_token, options={"verify_signature": False})  # Skip verification for demo
                
                email = payload.get("email")
                name = payload.get("name", email)
                
                # Get or create user
                user = await self._get_or_create_oauth_user(
                    email=email,
                    name=name,
                    provider=AuthProvider.GOOGLE,
                    provider_id=payload.get("sub")
                )
                
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Google authentication error: {e}")
            return None
    
    async def _authenticate_github(self, auth_code: Optional[str]) -> Optional[User]:
        """GitHub OAuth2 authentication"""
        # Placeholder implementation
        logger.warning("GitHub authentication not implemented yet")
        return None
    
    async def _authenticate_azure_ad(self, auth_code: Optional[str], id_token: Optional[str]) -> Optional[User]:
        """Azure AD authentication"""
        # Placeholder implementation
        logger.warning("Azure AD authentication not implemented yet")
        return None
    
    async def _get_or_create_oauth_user(
        self,
        email: str,
        name: str,
        provider: AuthProvider,
        provider_id: str
    ) -> Optional[User]:
        """Get existing OAuth user or create new one"""
        try:
            # Check if user exists
            user_key = f"user:email:{email}"
            user_data = self.redis_client.get(user_key)
            
            if user_data:
                user_dict = json.loads(user_data)
                
                # Update last login
                await self._update_last_login(user_dict["user_id"])
                
                return User(
                    user_id=user_dict["user_id"],
                    email=user_dict["email"],
                    name=user_dict["name"],
                    role=UserRole(user_dict["role"]),
                    auth_provider=AuthProvider(user_dict["auth_provider"]),
                    organization_id=user_dict.get("organization_id"),
                    team_id=user_dict.get("team_id"),
                    created_at=datetime.fromisoformat(user_dict["created_at"]),
                    last_login=datetime.fromisoformat(user_dict["last_login"]) if user_dict.get("last_login") else None,
                    is_active=user_dict.get("is_active", True),
                    permissions=self.role_permissions.get(UserRole(user_dict["role"]), set()),
                    metadata=user_dict.get("metadata", {})
                )
            
            # Create new user
            user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(email.encode()).hexdigest()[:8]}"
            
            # Default role for new users
            default_role = UserRole.VIEWER
            
            new_user = User(
                user_id=user_id,
                email=email,
                name=name,
                role=default_role,
                auth_provider=provider,
                organization_id=None,
                team_id=None,
                created_at=datetime.now(),
                last_login=datetime.now(),
                is_active=True,
                permissions=self.role_permissions.get(default_role, set()),
                metadata={"provider_id": provider_id}
            )
            
            # Save to Redis
            await self._save_user(new_user)
            
            return new_user
            
        except Exception as e:
            logger.error(f"Error getting/creating OAuth user: {e}")
            return None
    
    async def create_tokens(self, user: User) -> AuthToken:
        """Create JWT access and refresh tokens"""
        try:
            # Access token payload
            access_payload = {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions],
                "type": "access",
                "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
                "iat": datetime.utcnow()
            }
            
            # Refresh token payload
            refresh_payload = {
                "user_id": user.user_id,
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
                "iat": datetime.utcnow()
            }
            
            # Generate tokens
            access_token = jwt.encode(access_payload, self.secret_key, algorithm="HS256")
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm="HS256")
            
            # Store refresh token in Redis
            refresh_key = f"refresh_token:{user.user_id}"
            self.redis_client.setex(
                refresh_key,
                timedelta(days=self.refresh_token_expire_days),
                refresh_token
            )
            
            return AuthToken(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60
            )
            
        except Exception as e:
            logger.error(f"Error creating tokens: {e}")
            raise
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[AuthToken]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=["HS256"])
            
            if payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("user_id")
            
            # Check if refresh token is still valid in Redis
            refresh_key = f"refresh_token:{user_id}"
            stored_token = self.redis_client.get(refresh_key)
            
            if not stored_token or stored_token.decode() != refresh_token:
                return None
            
            # Get user
            user = await self.get_user(user_id)
            if not user or not user.is_active:
                return None
            
            # Create new tokens
            return await self.create_tokens(user)
            
        except Exception as e:
            logger.error(f"Error refreshing tokens: {e}")
            return None
    
    async def logout(self, user_id: str, access_token: str) -> bool:
        """Logout user and invalidate tokens"""
        try:
            # Blacklist access token
            blacklist_key = f"blacklist_token:{hashlib.sha256(access_token.encode()).hexdigest()}"
            self.redis_client.setex(blacklist_key, timedelta(hours=1), "1")
            
            # Remove refresh token
            refresh_key = f"refresh_token:{user_id}"
            self.redis_client.delete(refresh_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False
    
    async def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in user.permissions
    
    async def check_resource_access(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
        action: str
    ) -> bool:
        """Check if user can access specific resource"""
        try:
            # Basic permission check
            required_permission = f"{resource_type}:{action}"
            if not any(perm.value == required_permission for perm in user.permissions):
                return False
            
            # Resource-specific checks
            if resource_type == "sessions":
                return await self._check_session_access(user, resource_id, action)
            elif resource_type == "reports":
                return await self._check_report_access(user, resource_id, action)
            elif resource_type == "users":
                return await self._check_user_access(user, resource_id, action)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking resource access: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_key = f"user:{user_id}"
            user_data = self.redis_client.get(user_key)
            
            if not user_data:
                return None
            
            user_dict = json.loads(user_data)
            
            return User(
                user_id=user_dict["user_id"],
                email=user_dict["email"],
                name=user_dict["name"],
                role=UserRole(user_dict["role"]),
                auth_provider=AuthProvider(user_dict["auth_provider"]),
                organization_id=user_dict.get("organization_id"),
                team_id=user_dict.get("team_id"),
                created_at=datetime.fromisoformat(user_dict["created_at"]),
                last_login=datetime.fromisoformat(user_dict["last_login"]) if user_dict.get("last_login") else None,
                is_active=user_dict.get("is_active", True),
                permissions=self.role_permissions.get(UserRole(user_dict["role"]), set()),
                metadata=user_dict.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def _save_user(self, user: User):
        """Save user to Redis"""
        try:
            user_dict = asdict(user)
            user_dict["role"] = user.role.value
            user_dict["auth_provider"] = user.auth_provider.value
            user_dict["created_at"] = user.created_at.isoformat()
            if user.last_login:
                user_dict["last_login"] = user.last_login.isoformat()
            
            # Save by ID
            user_key = f"user:{user.user_id}"
            self.redis_client.set(user_key, json.dumps(user_dict))
            
            # Save by email for lookup
            email_key = f"user:email:{user.email}"
            email_data = {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "auth_provider": user.auth_provider.value,
                "organization_id": user.organization_id,
                "team_id": user.team_id,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active,
                "metadata": user.metadata
            }
            
            # For local auth, include password hash
            if user.auth_provider == AuthProvider.LOCAL and "password_hash" in user_dict:
                email_data["password_hash"] = user_dict["password_hash"]
            
            self.redis_client.set(email_key, json.dumps(email_data))
            
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            raise
    
    async def _update_last_login(self, user_id: str):
        """Update user's last login time"""
        try:
            user_key = f"user:{user_id}"
            user_data = self.redis_client.get(user_key)
            
            if user_data:
                user_dict = json.loads(user_data)
                user_dict["last_login"] = datetime.now().isoformat()
                self.redis_client.set(user_key, json.dumps(user_dict))
                
                # Also update email lookup
                email = user_dict.get("email")
                if email:
                    email_key = f"user:email:{email}"
                    email_data = self.redis_client.get(email_key)
                    if email_data:
                        email_dict = json.loads(email_data)
                        email_dict["last_login"] = datetime.now().isoformat()
                        self.redis_client.set(email_key, json.dumps(email_dict))
            
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            # Using hashlib for demo - in production use bcrypt or argon2
            password_hash_check = hashlib.sha256(password.encode()).hexdigest()
            return password_hash_check == password_hash
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            blacklist_key = f"blacklist_token:{hashlib.sha256(token.encode()).hexdigest()}"
            return self.redis_client.exists(blacklist_key)
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False
    
    async def _check_session_access(self, user: User, session_id: str, action: str) -> bool:
        """Check session-specific access"""
        try:
            # Get session info
            session_key = f"session:{session_id}:info"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                session_info = json.loads(session_data)
                
                # Users can access their own sessions
                if session_info.get("user_id") == user.user_id:
                    return True
                
                # Team leads can access team sessions
                if user.role == UserRole.TEAM_LEAD:
                    if session_info.get("team_id") == user.team_id:
                        return True
                
                # Org admins can access org sessions
                if user.role == UserRole.ORG_ADMIN:
                    if session_info.get("organization_id") == user.organization_id:
                        return True
                
                # Super admins can access everything
                if user.role == UserRole.SUPER_ADMIN:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking session access: {e}")
            return False
    
    async def _check_report_access(self, user: User, report_id: str, action: str) -> bool:
        """Check report-specific access"""
        # Similar logic to session access
        return True  # Simplified for now
    
    async def _check_user_access(self, user: User, target_user_id: str, action: str) -> bool:
        """Check user management access"""
        # Users can manage themselves
        if user.user_id == target_user_id:
            return True
        
        # Team leads can manage team members
        if user.role == UserRole.TEAM_LEAD and action in ["read"]:
            return True
        
        # Org admins can manage org users
        if user.role == UserRole.ORG_ADMIN:
            return True
        
        # Super admins can manage everyone
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        return False

# Singleton instance
auth_manager = AuthManager()