import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


async def register_and_login(client: AsyncClient) -> str:
    """Helper: register a user and return their access token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "attempt_user@example.com",
            "username": "attempt_user",
            "password": "TestPass123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "attempt_user", "password": "TestPass123"},
    )
    return login_resp.json()["access_token"]


async def create_problem(client: AsyncClient) -> int:
    """Helper: create a problem and return its ID."""
    resp = await client.post(
        "/api/v1/problems/",
        json={
            "title": "Test Attempt Problem",
            "description": "A problem for testing attempts",
            "difficulty": "easy",
        },
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_start_attempt(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register_and_login(client)
        problem_id = await create_problem(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/attempts/",
            headers=headers,
            json={"problem_id": problem_id, "language": "python"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "started"
    assert data["problem_id"] == problem_id


@pytest.mark.asyncio
async def test_submit_attempt(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register_and_login(client)
        problem_id = await create_problem(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Start
        start_resp = await client.post(
            "/api/v1/attempts/", headers=headers,
            json={"problem_id": problem_id},
        )
        attempt_id = start_resp.json()["id"]

        # Submit
        response = await client.post(
            f"/api/v1/attempts/{attempt_id}/submit", headers=headers,
            json={"code": "print('hello')", "language": "python"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "passed"
    assert data["code"] == "print('hello')"


@pytest.mark.asyncio
async def test_record_telemetry_event(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register_and_login(client)
        problem_id = await create_problem(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Start attempt
        start_resp = await client.post(
            "/api/v1/attempts/", headers=headers,
            json={"problem_id": problem_id},
        )
        attempt_id = start_resp.json()["id"]

        # Record event
        response = await client.post(
            f"/api/v1/attempts/{attempt_id}/telemetry/events", headers=headers,
            json={"event_type": "keystroke", "time_since_start_ms": 500, "data": {"key": "a"}},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "keystroke"


@pytest.mark.asyncio
async def test_record_telemetry_batch(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register_and_login(client)
        problem_id = await create_problem(client)
        headers = {"Authorization": f"Bearer {token}"}

        start_resp = await client.post(
            "/api/v1/attempts/", headers=headers,
            json={"problem_id": problem_id},
        )
        attempt_id = start_resp.json()["id"]

        # Batch record
        response = await client.post(
            f"/api/v1/attempts/{attempt_id}/telemetry/events/batch", headers=headers,
            json={
                "events": [
                    {"event_type": "keystroke", "time_since_start_ms": 100},
                    {"event_type": "keystroke", "time_since_start_ms": 200},
                    {"event_type": "undo", "time_since_start_ms": 300},
                ]
            },
        )

    assert response.status_code == 201
    assert response.json()["count"] == 3


@pytest.mark.asyncio
async def test_telemetry_summary(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register_and_login(client)
        problem_id = await create_problem(client)
        headers = {"Authorization": f"Bearer {token}"}

        start_resp = await client.post(
            "/api/v1/attempts/", headers=headers,
            json={"problem_id": problem_id},
        )
        attempt_id = start_resp.json()["id"]

        # Record some events
        await client.post(
            f"/api/v1/attempts/{attempt_id}/telemetry/events/batch", headers=headers,
            json={
                "events": [
                    {"event_type": "keystroke", "time_since_start_ms": 100},
                    {"event_type": "keystroke", "time_since_start_ms": 200},
                    {"event_type": "keystroke", "time_since_start_ms": 300},
                    {"event_type": "undo", "time_since_start_ms": 400},
                    {"event_type": "paste", "time_since_start_ms": 500},
                ]
            },
        )

        # Get summary
        response = await client.get(
            f"/api/v1/attempts/{attempt_id}/telemetry/summary", headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_keystrokes"] == 3
    assert data["total_undos"] == 1
    assert data["total_pastes"] == 1
    assert data["events_count"] == 5


@pytest.mark.asyncio
async def test_attempt_requires_auth(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/attempts/",
            json={"problem_id": 1},
        )
    assert response.status_code == 401