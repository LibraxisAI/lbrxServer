"""
Authentication and authorization for MLX LLM Server
"""
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthManager:
    """Manages API authentication"""

    def __init__(self):
        self.api_keys = set(config.api_keys)
        self.jwt_secret = config.jwt_secret
        self.jwt_algorithm = config.jwt_algorithm

    def verify_api_key(self, api_key: str) -> bool:
        """Verify if API key is valid"""
        return api_key in self.api_keys

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def generate_api_key(self) -> str:
        """Generate a new API key"""
        return f"lbrx_{secrets.token_urlsafe(32)}"


# Global auth manager
auth_manager = AuthManager()


async def verify_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """FastAPI dependency for authentication"""
    if not config.enable_auth:
        return {"authenticated": True, "method": "disabled"}

    token = credentials.credentials

    # Check if it's an API key
    if token.startswith("lbrx_"):
        if auth_manager.verify_api_key(token):
            return {"authenticated": True, "method": "api_key", "key": token}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Otherwise, treat as JWT
    payload = auth_manager.verify_token(token)
    return {"authenticated": True, "method": "jwt", "payload": payload}


async def optional_auth(credentials: HTTPAuthorizationCredentials | None = Security(security)) -> dict | None:
    """Optional authentication for public endpoints"""
    if not credentials:
        return None

    try:
        return await verify_auth(credentials)
    except HTTPException:
        return None
