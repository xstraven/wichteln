import sys
from pathlib import Path
from typing import Dict
import importlib

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import wichteln.database as database_module
import wichteln.main as main_module

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    global database_module, main_module

    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    try:
        await database_module.engine.dispose()
    except AttributeError:
        pass

    database_module = importlib.reload(database_module)
    main_module = importlib.reload(main_module)
    app = main_module.app

    await main_module.startup()

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
        try:
            await database_module.engine.dispose()
        except AttributeError:
            pass


@pytest.mark.asyncio
async def test_create_group_and_reveal(client: AsyncClient):
    payload = {
        "identifier": "SnowyCocoaPenguin",
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"},
        ],
        "illegalPairs": [{"giver": "Alice", "receiver": "Bob"}],
        "description": "Winter brunch exchange",
    }

    create_response = await client.post("/api/groups", json=payload)
    assert create_response.status_code == 201, create_response.text
    body = create_response.json()
    assert body["identifier"] == payload["identifier"]
    assert body["participantCount"] == 3
    assert body["illegalPairCount"] == 1

    assignments: Dict[str, str] = {}
    for participant in ["Alice", "Bob", "Charlie"]:
        reveal_response = await client.post(
            f"/api/groups/{payload['identifier']}/reveal",
            json={"name": participant},
        )
        assert reveal_response.status_code == 200, reveal_response.text
        result = reveal_response.json()
        assignments[result["participantName"]] = result["recipientName"]

    assert set(assignments.keys()) == {"Alice", "Bob", "Charlie"}
    assert set(assignments.values()) == {"Alice", "Bob", "Charlie"}
    for giver, receiver in assignments.items():
        assert giver != receiver
    assert assignments["Alice"] != "Bob"


@pytest.mark.asyncio
async def test_identifier_conflict_returns_409(client: AsyncClient):
    payload = {
        "identifier": "FrostyRibbonLantern",
        "participants": [
            {"name": "Jamie"},
            {"name": "Riley"},
        ],
        "illegalPairs": [],
    }

    first = await client.post("/api/groups", json=payload)
    assert first.status_code == 201, first.text

    second = await client.post("/api/groups", json=payload)
    assert second.status_code == 409
    assert "Identifier already exists" in second.json()["detail"]
