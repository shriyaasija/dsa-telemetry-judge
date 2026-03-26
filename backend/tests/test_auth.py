import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_user(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
                "full_name": "Test User"
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_user(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register first user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "duplicate",
                "password": "TestPass123"
            }
        )

        # Try to register same user again
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "duplicate",
                "password": "TestPass123"
            }
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "TestPass123"
            }
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "loginuser",
                "password": "TestPass123"
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrong@example.com",
                "username": "wrongpass",
                "password": "TestPass123"
            }
        )

        # Try login with wrong password
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "wrongpass",
                "password": "WrongPassword123"
            }
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "current@example.com",
                "username": "currentuser",
                "password": "TestPass123",
                "full_name": "Current User"
            }
        )

        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "currentuser",
                "password": "TestPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentuser"
    assert data["email"] == "current@example.com"
    assert data["full_name"] == "Current User"


@pytest.mark.asyncio
async def test_unauthorized_access(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to access protected endpoint without token
        response = await client.get("/api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

    assert response.status_code == 401
