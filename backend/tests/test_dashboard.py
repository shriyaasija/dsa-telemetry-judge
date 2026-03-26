import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


async def setup_user_with_attempts(client: AsyncClient) -> tuple[str, int]:
    """Helper: register user, create problem, do some attempts. Returns (token, problem_id)."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dashboard_user@example.com",
            "username": "dashboard_user",
            "password": "TestPass123",
        },
    )

    # Login
    login_resp = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "dashboard_user", "password": "TestPass123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create problem
    prob_resp = await client.post(
        "/api/v1/problems/",
        json={
            "title": "Dashboard Test Problem",
            "description": "A problem for dashboard testing",
            "difficulty": "easy",
        },
    )
    problem_id = prob_resp.json()["id"]

    # Start and submit an attempt (creates a solved attempt)
    start_resp = await client.post(
        "/api/v1/attempts/", headers=headers,
        json={"problem_id": problem_id, "language": "python"},
    )
    attempt_id = start_resp.json()["id"]

    await client.post(
        f"/api/v1/attempts/{attempt_id}/submit", headers=headers,
        json={"code": "print('solved')", "language": "python"},
    )

    # Start and abandon another attempt
    start_resp2 = await client.post(
        "/api/v1/attempts/", headers=headers,
        json={"problem_id": problem_id, "language": "python"},
    )
    attempt_id2 = start_resp2.json()["id"]

    await client.post(
        f"/api/v1/attempts/{attempt_id2}/abandon", headers=headers,
    )

    return token, problem_id


@pytest.mark.asyncio
async def test_get_dashboard_stats(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await setup_user_with_attempts(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/dashboard/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_attempts"] == 2
    assert data["total_solved"] == 1
    assert data["total_abandoned"] == 1
    assert data["solve_rate"] == 0.5
    assert len(data["recent_activity"]) == 2


@pytest.mark.asyncio
async def test_dashboard_requires_auth(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_stats(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await setup_user_with_attempts(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/v1/dashboard/stats/refresh", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_attempts"] == 2


@pytest.mark.asyncio
async def test_empty_dashboard(override_get_db):
    """A user with no attempts should get zeroed-out stats."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register a fresh user with no attempts
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "empty_user@example.com",
                "username": "empty_user",
                "password": "TestPass123",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "empty_user", "password": "TestPass123"},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/dashboard/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_attempts"] == 0
    assert data["total_solved"] == 0
    assert data["solve_rate"] == 0.0
    assert data["current_streak"] == 0
    assert data["recent_activity"] == []
