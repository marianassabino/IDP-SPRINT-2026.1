import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from infrastructure.persistence.database import AsyncSessionLocal
from main import app

BASE = "http://test"


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(text("TRUNCATE TABLE dictionary_entries, projects, refresh_tokens, users CASCADE"))
        await session.commit()


async def register_and_login(client: AsyncClient, email: str, password: str = "Senha@123") -> None:
    await client.post("/auth/register", json={"name": "Test", "last_name": "User", "email": email, "password": password})
    await client.post("/auth/login", json={"email": email, "password": password})


@pytest_asyncio.fixture
async def client_a():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        await register_and_login(c, "user_a@test.com")
        yield c


@pytest_asyncio.fixture
async def client_b():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        await register_and_login(c, "user_b@test.com")
        yield c


ENTRY = {"kind": "NORMALIZATION_PRESET", "name": "Preset A", "payload": {"from": "MP", "to": "Ministério Público"}}


# ── Global dictionary ──────────────────────────────────────────────────────────

async def test_create_global_entry(client_a: AsyncClient):
    resp = await client_a.post("/dictionary", json=ENTRY)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Preset A"
    assert data["project_id"] is None


async def test_create_global_duplicate_returns_409(client_a: AsyncClient):
    await client_a.post("/dictionary", json=ENTRY)
    resp = await client_a.post("/dictionary", json=ENTRY)
    assert resp.status_code == 409


async def test_list_global_entries(client_a: AsyncClient):
    await client_a.post("/dictionary", json=ENTRY)
    await client_a.post("/dictionary", json={**ENTRY, "name": "Preset B"})
    resp = await client_a.get("/dictionary")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


async def test_list_global_filter_by_kind(client_a: AsyncClient):
    await client_a.post("/dictionary", json=ENTRY)
    await client_a.post("/dictionary", json={**ENTRY, "name": "Cat A", "kind": "CATEGORY_LIST"})
    resp = await client_a.get("/dictionary?kind=NORMALIZATION_PRESET")
    assert resp.json()["total"] == 1


async def test_get_global_entry(client_a: AsyncClient):
    created = (await client_a.post("/dictionary", json=ENTRY)).json()
    resp = await client_a.get(f"/dictionary/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_global_not_found(client_a: AsyncClient):
    resp = await client_a.get("/dictionary/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_update_global_entry(client_a: AsyncClient):
    created = (await client_a.post("/dictionary", json=ENTRY)).json()
    resp = await client_a.patch(f"/dictionary/{created['id']}", json={"name": "Novo Nome"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novo Nome"


async def test_delete_global_entry(client_a: AsyncClient):
    created = (await client_a.post("/dictionary", json=ENTRY)).json()
    resp = await client_a.delete(f"/dictionary/{created['id']}")
    assert resp.status_code == 204
    assert (await client_a.get(f"/dictionary/{created['id']}")).status_code == 404


async def test_global_isolation_between_users(client_a: AsyncClient, client_b: AsyncClient):
    created = (await client_a.post("/dictionary", json=ENTRY)).json()
    resp = await client_b.get(f"/dictionary/{created['id']}")
    assert resp.status_code == 404


# ── Project-scoped dictionary ──────────────────────────────────────────────────

async def _create_project(client: AsyncClient) -> str:
    resp = await client.post("/projects", json={"name": "Meu Projeto", "description": "", "ai_context": ""})
    return resp.json()["id"]


async def test_create_project_entry(client_a: AsyncClient):
    project_id = await _create_project(client_a)
    resp = await client_a.post(f"/projects/{project_id}/dictionary", json=ENTRY)
    assert resp.status_code == 201
    assert resp.json()["project_id"] == project_id


async def test_project_entry_duplicate_returns_409(client_a: AsyncClient):
    project_id = await _create_project(client_a)
    await client_a.post(f"/projects/{project_id}/dictionary", json=ENTRY)
    resp = await client_a.post(f"/projects/{project_id}/dictionary", json=ENTRY)
    assert resp.status_code == 409


async def test_same_name_global_and_project_ok(client_a: AsyncClient):
    project_id = await _create_project(client_a)
    await client_a.post("/dictionary", json=ENTRY)
    resp = await client_a.post(f"/projects/{project_id}/dictionary", json=ENTRY)
    assert resp.status_code == 201


async def test_list_project_entries_isolated_from_global(client_a: AsyncClient):
    project_id = await _create_project(client_a)
    await client_a.post("/dictionary", json=ENTRY)
    await client_a.post(f"/projects/{project_id}/dictionary", json={**ENTRY, "name": "Só Projeto"})
    resp = await client_a.get(f"/projects/{project_id}/dictionary")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Só Projeto"


async def test_delete_project_entry(client_a: AsyncClient):
    project_id = await _create_project(client_a)
    created = (await client_a.post(f"/projects/{project_id}/dictionary", json=ENTRY)).json()
    resp = await client_a.delete(f"/projects/{project_id}/dictionary/{created['id']}")
    assert resp.status_code == 204
