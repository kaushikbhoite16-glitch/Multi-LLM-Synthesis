from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database.session import get_db

async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session
