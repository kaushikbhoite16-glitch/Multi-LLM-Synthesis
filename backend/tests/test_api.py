import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_api_models():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/models")
        assert res.status_code == 200
        models = res.json()
        assert len(models) >= 4

@pytest.mark.asyncio
async def test_api_analytics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/analytics")
        assert res.status_code == 200
        data = res.json()
        assert "kpis" in data
        assert "per_model" in data
        assert "quality_vs_cost" in data

@pytest.mark.asyncio
async def test_api_export_json():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/export?format=json")
        assert res.status_code == 200
        data = res.json()
        assert "records" in data
