import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_problem(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/problems/",
            json={
                "title": "Test Problem",
                "description": "This is a test problem description",
                "difficulty": "easy",
                "tags": "test,example"
            }
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Problem"
    assert data["slug"] == "test-problem"
    assert data["difficulty"] == "easy"


@pytest.mark.asyncio
async def test_list_problems(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/problems/",
            json={
                "title": "Problem 1",
                "description": "Description 1",
                "difficulty": "easy"
            }
        )
        
        # list problems
        response = await client.get("/api/v1/problems/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["problems"]) == 1


@pytest.mark.asyncio
async def test_get_problem_by_id(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # create
        create_response = await client.post(
            "/api/v1/problems/",
            json={
                "title": "Get Test",
                "description": "Test description",
                "difficulty": "medium"
            }
        )
        problem_id = create_response.json()["id"]
        
        # get
        response = await client.get(f"/api/v1/problems/{problem_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Get Test"


@pytest.mark.asyncio
async def test_update_problem(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # create
        create_response = await client.post(
            "/api/v1/problems/",
            json={
                "title": "Original Title",
                "description": "Original description",
                "difficulty": "easy"
            }
        )
        problem_id = create_response.json()["id"]
        
        # update
        response = await client.put(
            f"/api/v1/problems/{problem_id}",
            json={"title": "Updated Title"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_problem(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # create
        create_response = await client.post(
            "/api/v1/problems/",
            json={
                "title": "To Delete",
                "description": "Will be deleted",
                "difficulty": "hard"
            }
        )
        problem_id = create_response.json()["id"]
        
        # celete
        response = await client.delete(f"/api/v1/problems/{problem_id}")
    
    assert response.status_code == 204