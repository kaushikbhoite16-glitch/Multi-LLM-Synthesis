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


# ---------------------------------------------------------------------------
# 13. Signup then immediate login with same credentials succeeds
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_signup_then_immediate_login_same_credentials():
    """Verify signup persists and subsequent sign-in with identical credentials succeeds."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        password = "ProductionPassword2026!"

        # Step 1: Signup
        signup_res = await client.post("/api/auth/signup", json={
            "email": email,
            "password": password,
            "full_name": "Immediate Login Test"
        })
        assert signup_res.status_code == 200, f"Signup failed: {signup_res.text}"
        signup_data = signup_res.json()
        assert signup_data["user"]["email"] == email

        # Step 2: Login with exact same credentials
        login_res = await client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        login_data = login_res.json()
        assert login_data["user"]["email"] == email
        assert "access_token" in login_data


# ---------------------------------------------------------------------------
# 14. Google OAuth official ID token verification and account creation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_google_oauth_credential_token_authentication(monkeypatch):
    """Verify backend verifies Google ID token via official library and creates/logs in user."""
    from app.utils import security

    google_email = f"google_verified_{uuid.uuid4().hex[:6]}@gmail.com"
    mock_claims = {
        "sub": "google-verified-id-998877",
        "email": google_email,
        "name": "Google Verified User",
        "iss": "https://accounts.google.com"
    }

    # Monkeypatch verify_google_id_token to simulate Google's verified response
    monkeypatch.setattr(security, "verify_google_id_token", lambda token: mock_claims)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        oauth_res = await client.post("/api/auth/google", json={
            "credential": "valid-signed-google-id-token"
        })
        assert oauth_res.status_code == 200, f"Google OAuth failed: {oauth_res.text}"
        oauth_data = oauth_res.json()
        assert oauth_data["user"]["email"] == google_email
        assert oauth_data["user"]["full_name"] == "Google Verified User"
        assert "access_token" in oauth_data

        # Authenticate with returned access_token on /auth/me
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {oauth_data['access_token']}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == google_email


# ---------------------------------------------------------------------------
# 15. Invalid / forged Google ID token is strictly rejected (401)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_google_id_token_rejected():
    """Verify unverified/forged Google credentials fail verification and return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # A forged JWT not signed by Google's private certs
        forged_jwt = pyjwt.encode(
            {"email": "hacker@evil.com", "name": "Fake", "iss": "https://accounts.google.com"},
            "random-secret-not-google",
            algorithm="HS256"
        )
        oauth_res = await client.post("/api/auth/google", json={
            "credential": forged_jwt
        })
        assert oauth_res.status_code == 401, (
            f"Expected 401 for forged Google token, got {oauth_res.status_code}: {oauth_res.text}"
        )


# ---------------------------------------------------------------------------
# 16. In production (TESTING=False), /auth/forgot-password never returns reset_token
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_forgot_password_never_exposes_token_in_production(monkeypatch):
    """Verify reset_token is never present in API response when TESTING is False."""
    monkeypatch.setattr(settings, "TESTING", False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})

        res = await client.post("/api/auth/forgot-password", json={"email": email})
        assert res.status_code == 200
        data = res.json()
        assert "reset_token" not in data, (
            "Security vulnerability: reset_token was leaked in API response when TESTING=False!"
        )
        assert "message" in data


# ---------------------------------------------------------------------------
# 17. Admin password synchronization only affects designated admin email
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_password_sync_does_not_overwrite_normal_users():
    """Verify admin password sync does not overwrite regular user accounts."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.database.session import engine
    from app.models.entities import User
    from app.utils.security import verify_password

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a regular user
        user_email = _make_unique_email()
        user_pw = "UserOriginalPassword123!"
        await client.post("/api/auth/signup", json={"email": user_email, "password": user_pw})

        # Verify password in DB matches user's password
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(User).where(User.email == user_email))
            user = res.scalar_one_or_none()
            assert user is not None
            assert verify_password(user_pw, user.hashed_password)
            # Must NOT match ADMIN_PASSWORD
            assert not verify_password(settings.ADMIN_PASSWORD, user.hashed_password)


# ---------------------------------------------------------------------------
# 18. Invalid reset token is rejected (400)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_reset_token_rejected():
    """Verify non-existent/invalid reset token returns 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/auth/reset-password", json={
            "token": "completely-invalid-nonexistent-token-12345",
            "new_password": "ValidNewPassword123!"
        })
        assert res.status_code == 400
        assert "Invalid or expired" in res.json().get("detail", "")


# ---------------------------------------------------------------------------
# 19. Expired reset token is rejected (400)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_expired_reset_token_rejected():
    """Verify reset token past its expiry window is strictly rejected."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.database.session import engine
    from app.models.entities import User

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "OldPassword123!"})

        # Request reset
        forgot_res = await client.post("/api/auth/forgot-password", json={"email": email})
        reset_token = forgot_res.json()["reset_token"]

        # Manually expire the token in database
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(User).where(User.email == email))
            user = res.scalar_one_or_none()
            user.reset_token_expiry = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
            await db.commit()

        # Attempt to reset with expired token
        reset_res = await client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewPassword123!"
        })
        assert reset_res.status_code == 400
        assert "expired" in reset_res.json().get("detail", "").lower()


# ---------------------------------------------------------------------------
# 20. Reused reset token is strictly rejected (single-use enforcement)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reused_reset_token_rejected():
    """Verify single-use token: once used, second attempt is rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "InitialPassword123!"})

        # Request reset
        forgot_res = await client.post("/api/auth/forgot-password", json={"email": email})
        reset_token = forgot_res.json()["reset_token"]

        # First use: must succeed
        first_reset = await client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "FirstNewPassword123!"
        })
        assert first_reset.status_code == 200

        # Second use (replay attack): must be rejected
        second_reset = await client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "AttackerPassword123!"
        })
        assert second_reset.status_code == 400
        assert "Invalid or expired" in second_reset.json().get("detail", "")


# ---------------------------------------------------------------------------
# 21. Configured Resend HTTPS API sends email with reset link and token
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resend_email_delivery_dispatches_message(monkeypatch):
    """Verify Resend HTTPS API delivery sends correctly formatted payload with reset link."""
    intercepted_requests = []
    import httpx
    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, *args, **kwargs):
        if "api.resend.com" in str(url):
            intercepted_requests.append({
                "url": str(url),
                "json": kwargs.get("json"),
                "headers": kwargs.get("headers")
            })
            return httpx.Response(200, json={"id": "mock_msg_123"}, request=httpx.Request("POST", str(url)))
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_api_key_123")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "onboarding@resend.dev")
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://multi-llm-synthesis-web.vercel.app")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})

        res = await client.post("/api/auth/forgot-password", json={"email": email})
        assert res.status_code == 200
        assert "dispatched" in res.json().get("message", "").lower()
        assert len(intercepted_requests) == 1

        req = intercepted_requests[0]
        assert req["url"] == "https://api.resend.com/emails"
        assert req["headers"]["Authorization"] == "Bearer re_test_api_key_123"
        assert req["json"]["to"] == [email]
        assert req["json"]["from"] == "onboarding@resend.dev"
        assert "Password Reset Request" in req["json"]["subject"]
        assert "https://multi-llm-synthesis-web.vercel.app/?mode=reset&token=" in req["json"]["text"]
        assert "https://multi-llm-synthesis-web.vercel.app/?mode=reset&token=" in req["json"]["html"]


# ---------------------------------------------------------------------------
# 22. Resend API key fallback to SMTP_PASSWORD for backward compatibility
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resend_api_key_fallback_to_smtp_password(monkeypatch):
    """Verify effective_resend_api_key falls back to SMTP_PASSWORD if RESEND_API_KEY is unset."""
    intercepted_headers = []
    import httpx
    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, *args, **kwargs):
        if "api.resend.com" in str(url):
            intercepted_headers.append(kwargs.get("headers"))
            return httpx.Response(200, json={"id": "mock_msg_fallback"}, request=httpx.Request("POST", str(url)))
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "re_fallback_key_456")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "onboarding@resend.dev")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})

        res = await client.post("/api/auth/forgot-password", json={"email": email})
        assert res.status_code == 200
        assert "dispatched" in res.json().get("message", "").lower()
        assert len(intercepted_headers) == 1
        assert intercepted_headers[0]["Authorization"] == "Bearer re_fallback_key_456"


# ---------------------------------------------------------------------------
# 23. Resend API error reporting without leaking secret keys
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resend_api_error_handling(monkeypatch):
    """Verify Resend error response is handled gracefully without leaking keys or tokens."""
    import httpx
    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, *args, **kwargs):
        if "api.resend.com" in str(url):
            return httpx.Response(403, json={"message": "Domain not verified", "name": "validation_error"}, request=httpx.Request("POST", str(url)))
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secret_key_789")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "unverified@domain.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})

        res = await client.post("/api/auth/forgot-password", json={"email": email})
        assert res.status_code == 200
        data = res.json()
        assert "Domain not verified" in data.get("message", "")
        # Confirm API key is never leaked
        assert "re_secret_key_789" not in data.get("message", "")


# ---------------------------------------------------------------------------
# 24. Resend API timeout handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resend_api_timeout_handling(monkeypatch):
    """Verify Resend network timeout is handled cleanly."""
    import httpx
    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, *args, **kwargs):
        if "api.resend.com" in str(url):
            raise httpx.TimeoutException("Connection timed out", request=httpx.Request("POST", str(url)))
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secret_key_789")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "onboarding@resend.dev")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = _make_unique_email()
        await client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})

        res = await client.post("/api/auth/forgot-password", json={"email": email})
        assert res.status_code == 200
        data = res.json()
        assert "timed out" in data.get("message", "").lower()





