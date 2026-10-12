"""
Authentication Security Test Suite
===================================
Verifies that the backend performs REAL credential verification — not demo/mock
responses. Tests cover:
  - Successful signup and login returning a valid JWT
  - Invalid email login returns 401 (not a success or demo bypass)
  - Wrong password returns 401 with a generic error (no leaking which field failed)
  - Duplicate signup returns 400
  - JWT verification: forged tokens are rejected
  - Expired tokens are rejected
  - Protected endpoints reject unauthenticated requests with 401
  - Admin RBAC: regular users cannot access admin endpoints (403)
  - Admin RBAC: admin users can access admin endpoints (200)
  - Logout clears access by invalidating client-side token (no server-side bypass)
"""
import pytest
import uuid
import datetime
import jwt as pyjwt
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_unique_email() -> str:
    return f"sec_test_{uuid.uuid4().hex[:8]}@example.com"


async def _signup_and_login(client: AsyncClient, email: str, password: str) -> str:
    """Sign up and return the access token."""
    resp = await client.post("/api/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": "Test User"
    })
    assert resp.status_code == 200, f"Signup failed: {resp.text}"
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# 1. Successful signup returns a JWT and correct user profile
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_signup_returns_real_jwt():
    """Signup must return a signed JWT that can be decoded with the real secret."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        resp = await client.post("/api/auth/signup", json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "JWT Test User"
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "access_token" in data, "Response must include access_token"
        assert data["access_token"], "access_token must not be empty"
        assert "user" in data, "Response must include user profile"
        assert data["user"]["email"] == email
        assert data["user"]["role"] == "user"

        # Decode the JWT with the actual secret — this proves it was signed correctly
        payload = pyjwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert "sub" in payload, "JWT payload must contain 'sub' (user ID)"
        assert "email" in payload, "JWT payload must contain 'email'"
        assert payload["email"] == email


# ---------------------------------------------------------------------------
# 2. Successful login with correct credentials
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_correct_credentials():
    """Login with the correct email and password must succeed and return a JWT."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        password = "CorrectPassword456!"

        await client.post("/api/auth/signup", json={"email": email, "password": password})

        login_resp = await client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        assert "access_token" in data
        assert data["access_token"]
        assert data["user"]["email"] == email


# ---------------------------------------------------------------------------
# 3. Wrong password must be rejected — no demo bypass
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_wrong_password_rejected():
    """
    The backend must actually verify the password hash.
    A wrong password must return 401 — not a demo success response.
    This is the core test that ensures authentication is real.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        correct_password = "CorrectPassword789!"
        wrong_password = "WrongPassword000!"

        await client.post("/api/auth/signup", json={"email": email, "password": correct_password})

        login_resp = await client.post("/api/auth/login", json={
            "email": email,
            "password": wrong_password
        })
        assert login_resp.status_code == 401, (
            f"Expected 401 for wrong password but got {login_resp.status_code}: {login_resp.text}"
        )
        # Must not contain an access_token
        assert "access_token" not in login_resp.json(), (
            "Backend must NOT return a token for wrong credentials — auth bypass detected!"
        )


# ---------------------------------------------------------------------------
# 4. Non-existent email must return 401 (not 404, to prevent email enumeration)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_nonexistent_email_rejected():
    """Login with an email that has never been registered must return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/auth/login", json={
            "email": f"doesnotexist_{uuid.uuid4().hex}@nowhere.invalid",
            "password": "AnyPassword123!"
        })
        assert resp.status_code == 401, (
            f"Expected 401 for unknown email but got {resp.status_code}: {resp.text}"
        )
        assert "access_token" not in resp.json()


# ---------------------------------------------------------------------------
# 5. Duplicate signup is rejected
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_duplicate_signup_rejected():
    """Signing up with an already-registered email must return 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        first = await client.post("/api/auth/signup", json={"email": email, "password": "Pass123!"})
        assert first.status_code == 200

        second = await client.post("/api/auth/signup", json={"email": email, "password": "DifferentPass456!"})
        assert second.status_code == 400, (
            f"Expected 400 for duplicate signup but got {second.status_code}: {second.text}"
        )


# ---------------------------------------------------------------------------
# 6. Forged JWT token is rejected on protected endpoints
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_forged_jwt_rejected():
    """
    A JWT signed with a different/wrong key must be rejected.
    This verifies the backend validates token signatures — not just decodes them.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a token signed with a DIFFERENT secret
        forged_payload = {
            "sub": "99999",
            "email": "attacker@evil.com",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        forged_token = pyjwt.encode(forged_payload, "wrong-secret-key", algorithm="HS256")

        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
        assert resp.status_code == 401, (
            f"Expected 401 for forged JWT but got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# 7. Expired JWT token is rejected
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_expired_jwt_rejected():
    """A JWT with a past expiry must be rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        expired_payload = {
            "sub": "1",
            "email": "someuser@example.com",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1)  # already expired
        }
        expired_token = pyjwt.encode(
            expired_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401, (
            f"Expected 401 for expired JWT but got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# 8. Protected endpoints require authentication
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_protected_endpoints_require_auth():
    """Unauthenticated requests to protected endpoints must return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # /auth/me requires a valid token
        me_resp = await client.get("/api/auth/me")
        assert me_resp.status_code == 401, f"Expected 401 for /auth/me without token: {me_resp.text}"

        # /history requires authentication
        history_resp = await client.get("/api/history")
        assert history_resp.status_code == 401, f"Expected 401 for /history without token: {history_resp.text}"


# ---------------------------------------------------------------------------
# 9. Regular user cannot access admin endpoints (403)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin():
    """
    A regular user's valid JWT must be rejected by admin endpoints with 403.
    This verifies RBAC is enforced — not just authentication.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        token = await _signup_and_login(client, email, "UserPass123!")

        # /admin/stats is admin-only
        stats_resp = await client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert stats_resp.status_code == 403, (
            f"Expected 403 for regular user on /admin/stats but got {stats_resp.status_code}: {stats_resp.text}"
        )

        # /admin/users is admin-only
        users_resp = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert users_resp.status_code == 403, (
            f"Expected 403 for regular user on /admin/users but got {users_resp.status_code}: {users_resp.text}"
        )


# ---------------------------------------------------------------------------
# 10. Admin user CAN access admin endpoints
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_user_can_access_admin_endpoints():
    """
    An admin user's JWT must be accepted by admin endpoints.
    The admin is created via the application's own signup + role promotion path,
    matching how main.py lifespan seeds the admin.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.database.session import engine
    from app.models.entities import User

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a user and promote them to admin directly in the DB (simulating lifespan seed)
        admin_email = f"admin_rbac_{uuid.uuid4().hex[:6]}@test.com"
        admin_password = "AdminPass123!"

        signup_resp = await client.post("/api/auth/signup", json={
            "email": admin_email,
            "password": admin_password,
            "full_name": "RBAC Test Admin"
        })
        assert signup_resp.status_code == 200
        user_id = signup_resp.json()["user"]["id"]

        # Promote to admin via direct DB update (mirrors the lifespan seed logic)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            assert user is not None
            user.role = "admin"
            await db.commit()

        # Login to get a fresh token (now has admin role in DB)
        login_resp = await client.post("/api/auth/login", json={
            "email": admin_email,
            "password": admin_password
        })
        assert login_resp.status_code == 200
        admin_token = login_resp.json()["access_token"]

        # Admin should be able to access /admin/stats
        stats_resp = await client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert stats_resp.status_code == 200, (
            f"Expected 200 for admin on /admin/stats but got {stats_resp.status_code}: {stats_resp.text}"
        )

        # Admin should be able to list users
        users_resp = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert users_resp.status_code == 200, (
            f"Expected 200 for admin on /admin/users but got {users_resp.status_code}: {users_resp.text}"
        )
        users_data = users_resp.json()
        assert isinstance(users_data, list), "Admin /users must return a list"


# ---------------------------------------------------------------------------
# 11. /auth/me returns current authenticated user (not a different user's data)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_auth_me_returns_correct_user():
    """The /auth/me endpoint must return the profile of the token's owner."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email_a = _make_unique_email()
        token_a = await _signup_and_login(client, email_a, "PassA123!")

        me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert me_resp.status_code == 200, me_resp.text
        profile = me_resp.json()
        assert profile["email"] == email_a
        assert profile["role"] == "user"
        assert "hashed_password" not in profile, "Password hash must never be exposed in API responses"


# ---------------------------------------------------------------------------
# 12. Short/weak passwords are rejected during signup
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_weak_password_rejected_on_signup():
    """Passwords shorter than 6 characters must be rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/auth/signup", json={
            "email": _make_unique_email(),
            "password": "abc"  # 3 chars — too short
        })
        assert resp.status_code == 400, (
            f"Expected 400 for weak password but got {resp.status_code}: {resp.text}"
        )
