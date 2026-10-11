from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy import select

from app.database.session import get_db
from app.utils.security import decode_access_token
from app.models.entities import User as UserEntity

security_bearer = HTTPBearer(auto_error=False)

async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session

async def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_session)
) -> Optional[UserEntity]:
    """Retrieves user if valid Bearer token provided, otherwise None."""
    if not auth or not auth.credentials:
        return None
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload["sub"])
        res = await db.execute(select(UserEntity).where(UserEntity.id == user_id))
        user = res.scalar_one_or_none()
        return user
    except Exception:
        return None

async def get_current_user(
    user: Optional[UserEntity] = Depends(get_optional_user)
) -> UserEntity:
    """Enforces authentication; raises 401 Unauthorized if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or have expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
