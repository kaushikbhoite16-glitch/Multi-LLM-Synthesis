import pytest
from app.config import settings
from app.database.session import engine, Base
import app.models.entities  # Ensure all models are registered on Base.metadata

# Enable TESTING mode for unit test suite so security assertions can inspect reset tokens
settings.TESTING = True

@pytest.fixture(autouse=True, scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
async def init_test_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
