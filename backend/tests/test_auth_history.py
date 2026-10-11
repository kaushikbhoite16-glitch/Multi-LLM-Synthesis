import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_auth_and_history_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create User A
        email_a = f"usera_{uuid.uuid4().hex[:6]}@example.com"
        signup_a = await client.post("/api/auth/signup", json={
            "email": email_a,
            "password": "Password123!",
            "full_name": "User Alpha"
        })
        assert signup_a.status_code == 200, signup_a.text
        data_a = signup_a.json()
        token_a = data_a["access_token"]
        assert token_a is not None
        assert data_a["user"]["email"] == email_a

        # 2. Create User B
        email_b = f"userb_{uuid.uuid4().hex[:6]}@example.com"
        signup_b = await client.post("/api/auth/signup", json={
            "email": email_b,
            "password": "Password456!",
            "full_name": "User Beta"
        })
        assert signup_b.status_code == 200, signup_b.text
        data_b = signup_b.json()
        token_b = data_b["access_token"]
        assert token_b is not None

        # 3. Test /auth/me for User A
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == email_a

        # 4. User A executes a query in simulation mode
        run_res = await client.post(
            "/api/run",
            json={
                "query": "Explain database indexing strategies",
                "execution_mode": "simulation"
            },
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert run_res.status_code == 200
        run_data = run_res.json()
        query_id = run_data["query_id"]
        assert query_id is not None
        assert run_data["is_mock"] is True
        assert run_data["execution_mode"] == "simulation"
        assert run_data["total_pipeline_cost"] == 0.0

        # 5. User A checks their history -> should see the query
        hist_a = await client.get("/api/history", headers={"Authorization": f"Bearer {token_a}"})
        assert hist_a.status_code == 200
        items_a = hist_a.json()
        found = [it for it in items_a if it["id"] == query_id]
        assert len(found) == 1
        assert found[0]["execution_mode"] == "simulation"
        assert found[0]["total_cost"] == 0.0

        # 6. User B checks their history -> MUST NOT see User A's query (Strict Data Isolation)
        hist_b = await client.get("/api/history", headers={"Authorization": f"Bearer {token_b}"})
        assert hist_b.status_code == 200
        items_b = hist_b.json()
        assert not any(it["id"] == query_id for it in items_b)

        # 7. User B tries to view or rename User A's query -> MUST return 403 Forbidden
        detail_b = await client.get(f"/api/history/{query_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert detail_b.status_code == 403

        rename_b = await client.put(f"/api/history/{query_id}/rename", json={"title": "Hacked Title"}, headers={"Authorization": f"Bearer {token_b}"})
        assert rename_b.status_code == 403

        delete_b = await client.delete(f"/api/history/{query_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert delete_b.status_code == 403

        # 8. User A renames their query
        rename_a = await client.put(f"/api/history/{query_id}/rename", json={"title": "Custom Indexing Guide"}, headers={"Authorization": f"Bearer {token_a}"})
        assert rename_a.status_code == 200
        assert rename_a.json()["title"] == "Custom Indexing Guide"

        # 9. User A retrieves full detail without calling APIs again
        detail_a = await client.get(f"/api/history/{query_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert detail_a.status_code == 200
        detail_data = detail_a.json()
        assert detail_data["query_id"] == query_id
        assert detail_data["synthesis"] is not None

        # 10. User A deletes the query
        del_a = await client.delete(f"/api/history/{query_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert del_a.status_code == 200

        # Verify it's deleted
        detail_deleted = await client.get(f"/api/history/{query_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert detail_deleted.status_code == 404

@pytest.mark.asyncio
async def test_forgot_and_reset_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"recovery_{uuid.uuid4().hex[:6]}@example.com"
        await client.post("/api/auth/signup", json={
            "email": email,
            "password": "OldPassword123!"
        })

        # Request reset
        forgot_res = await client.post("/api/auth/forgot-password", json={"email": email})
        assert forgot_res.status_code == 200
        reset_token = forgot_res.json().get("reset_token")
        assert reset_token is not None

        # Reset password
        reset_res = await client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewSecurePassword456!"
        })
        assert reset_res.status_code == 200

        # Login with new password
        login_res = await client.post("/api/auth/login", json={
            "email": email,
            "password": "NewSecurePassword456!"
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()
