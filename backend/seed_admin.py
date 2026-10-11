import asyncio
import sys
sys.path.insert(0, '.')
from app.database.session import engine, Base
from app.models.entities import User
from app.utils.security import hash_password
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        existing = res.scalar_one_or_none()
        if existing:
            existing.role = 'admin'
            existing.hashed_password = hash_password(settings.ADMIN_PASSWORD)
            existing.is_active = True
            await db.commit()
            print(f"Updated existing admin user: {settings.ADMIN_EMAIL}")
        else:
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name="System Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print(f"Created initial admin user: {settings.ADMIN_EMAIL}")
        print("Admin seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_admin())
