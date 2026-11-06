import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router
from app.database.session import engine, Base
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Ensure administrator user exists and has admin role
    try:
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        from app.models.entities import User
        from app.utils.security import hash_password
        
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as db:
            admin_email = settings.ADMIN_EMAIL.strip().lower()
            res = await db.execute(select(User).where(User.email == admin_email))
            existing_admin = res.scalar_one_or_none()
            if existing_admin:
                changed = False
                if existing_admin.role != "admin":
                    existing_admin.role = "admin"
                    changed = True
                # Update password if ADMIN_PASSWORD is set and non-empty
                if settings.ADMIN_PASSWORD:
                    existing_admin.hashed_password = hash_password(settings.ADMIN_PASSWORD)
                    changed = True
                if not existing_admin.is_active:
                    existing_admin.is_active = True
                    changed = True
                if changed:
                    await db.commit()
            else:
                new_admin = User(
                    email=admin_email,
                    hashed_password=hash_password(settings.ADMIN_PASSWORD),
                    full_name="System Administrator",
                    role="admin",
                    is_active=True
                )
                db.add(new_admin)
                await db.commit()
        logger.info(f"Administrator account verified: {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.warning(f"Administrator auto-seed notice: {e}")

    # Initialize Hybrid RAG vector store and seed collections if empty
    try:
        from app.rag.seed_data import ensure_seed_data, sync_seed_documents_to_db
        ensure_seed_data()
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as db:
            await sync_seed_documents_to_db(db)
        logger.info("Hybrid RAG vector store & knowledge bases verified.")
    except Exception as e:
        logger.warning(f"RAG seed data initialization notice: {e}")


    logger.info(f"Database schema initialized successfully. Mock mode: {settings.MOCK_MODE or not bool(settings.OPENROUTER_API_KEY)}")
    yield

    await engine.dispose()

app = FastAPI(
    title="Multi-LLM Response Evaluation and Adaptive Answer Synthesis",
    description="Full-stack research experimentation platform for multi-criteria LLM evaluation and adaptive answer synthesis.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend and deployment domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://multi-llm-synthesis-web.vercel.app",
        "https://multi-llm-synthesis.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "service": "Multi-LLM Response Evaluation and Adaptive Answer Synthesis API",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "rag_stats": f"{settings.API_V1_STR}/rag/stats"
    }

@app.get("/health")
async def healthcheck():
    return {
        "status": "healthy",
        "service": "Multi-LLM Evaluation and Synthesis System",
        "has_openrouter_key": bool(settings.OPENROUTER_API_KEY),
        "database": settings.DATABASE_URL.split("://")[0]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
