import pytest
import io
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.rag.seed_data import ensure_seed_data

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    ensure_seed_data()

@pytest.mark.asyncio
async def test_rag_stats_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/rag/stats")
        assert res.status_code == 200
        data = res.json()
        assert "collections" in data
        assert "general_knowledge" in data["collections"]
        assert "academic_knowledge" in data["collections"]
        assert "dynamic_web_cache" in data["collections"]
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_rag_retrieve_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "query": "virtual memory page tables operating systems",
            "top_k": 3,
            "sources": ["general", "academic", "web"]
        }
        res = await client.post("/api/rag/retrieve", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "evidence" in data
        assert "count" in data
        assert isinstance(data["evidence"], list)

@pytest.mark.asyncio
async def test_rag_document_upload_and_delete_workflow():
    import uuid
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Upload a text document with unique content to test full indexing cycle
        unique_token = uuid.uuid4().hex
        file_content = f"Binary search trees ({unique_token}) enforce left < root < right ordering property.".encode("utf-8")
        files = {
            "file": (f"bst_{unique_token[:6]}.txt", io.BytesIO(file_content), "text/plain")
        }
        data = {
            "title": f"BST Notes {unique_token[:6]}",
            "source_type": "general"
        }
        upload_res = await client.post("/api/rag/documents/upload", files=files, data=data)
        assert upload_res.status_code == 200
        upload_json = upload_res.json()
        assert upload_json["status"] in ("active", "indexed")
        doc_id = upload_json["document_id"]
        assert upload_json["chunk_count"] >= 1

        # 2. List documents
        list_res = await client.get("/api/rag/documents")
        assert list_res.status_code == 200
        docs_data = list_res.json()
        assert "documents" in docs_data
        docs = docs_data["documents"]
        assert any(d["id"] == doc_id for d in docs)

        # 3. Delete document
        del_res = await client.delete(f"/api/rag/documents/{doc_id}")
        assert del_res.status_code == 200
        del_json = del_res.json()
        assert del_json["status"] == "deleted"
        assert del_json["document_id"] == doc_id

@pytest.mark.asyncio
async def test_rag_academic_search_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/rag/academic/search", json={"query": "quantum computing", "max_results": 1})
        assert res.status_code == 200
        data = res.json()
        assert "papers" in data
        assert isinstance(data["papers"], dict)
        assert "arxiv" in data["papers"]
        assert "openalex" in data["papers"]
        assert "crossref" in data["papers"]

@pytest.mark.asyncio
async def test_rag_prune_web_cache():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/rag/prune", json={"older_than_days": 30})
        assert res.status_code == 200
        assert "pruned_count" in res.json()
