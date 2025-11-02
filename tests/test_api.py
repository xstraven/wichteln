import sys
from pathlib import Path
from typing import Dict
import importlib
import os
import uuid
from dotenv import load_dotenv

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import wichteln.database as database_module
import wichteln.main as main_module

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file for testing
load_dotenv(PROJECT_ROOT / ".env")


def unique_identifier():
    """Generate a unique identifier for tests (3+ PascalCase words)"""
    # Use UUID to select from large word pools, ensuring uniqueness per test run
    # Format: PrefixWordSuffixAdverb (e.g., TestCozyPineGently)
    prefixes = ["Test", "Try", "Temp", "Check", "Create", "Build", "Make", "Start"]
    words = [
        "Cozy", "Frosty", "Snowy", "Jolly", "Happy", "Merry", "Shiny", "Bright",
        "Vivid", "Magic", "Eager", "Witty", "Smart", "Quick", "Swift", "Rapid",
        "Gentle", "Soft", "Warm", "Cool", "Clear", "Bold", "Grand", "Noble",
        "Noble", "Mighty", "Strong", "Keen", "Sure", "True", "Fine", "Good"
    ]
    suffixes = [
        "Pine", "Oak", "Tree", "Snow", "Carol", "Bells", "Star", "Angel",
        "Gift", "Heart", "Peace", "Joy", "Cheer", "Festive", "Holly", "Wreath",
        "Light", "Flame", "Frost", "Wind", "Storm", "Cloud", "Moon", "Sun",
        "Dream", "Hope", "Faith", "Love", "Song", "Dance", "Waltz", "Spirit"
    ]
    adverbs = [
        "Gently", "Softly", "Freely", "Kindly", "Bravely", "Boldly", "Swiftly", "Slowly",
        "Brightly", "Darkly", "Warmly", "Coolly", "Gladly", "Sadly", "Wisely", "Purely"
    ]

    # Use UUID integer representation to extract unique indices
    uuid_obj = uuid.uuid4()
    uuid_int = uuid_obj.int
    prefix_idx = (uuid_int >> 0) % len(prefixes)
    word_idx = (uuid_int >> 16) % len(words)
    suffix_idx = (uuid_int >> 32) % len(suffixes)
    adverb_idx = (uuid_int >> 48) % len(adverbs)

    prefix = prefixes[prefix_idx]
    word = words[word_idx]
    suffix = suffixes[suffix_idx]
    adverb = adverbs[adverb_idx]

    return f"{prefix}{word}{suffix}{adverb}"


@pytest_asyncio.fixture
async def client(monkeypatch):
    global database_module, main_module

    # Use POSTGRES_CONNECT_STRING from .env or environment
    postgres_url = os.getenv(
        "POSTGRES_CONNECT_STRING",
        os.getenv("DATABASE_URL", "postgresql+psycopg://localhost/wichteln_test")
    )

    # Ensure async driver is used
    if postgres_url.startswith("postgresql://"):
        postgres_url = postgres_url.replace("postgresql://", "postgresql+psycopg://")
    elif postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql+psycopg://")

    monkeypatch.setenv("DATABASE_URL", postgres_url)

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
async def test_health_check(client: AsyncClient):
    """Test that the health check endpoint works"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_group_basic(client: AsyncClient):
    """Test basic group creation with minimum required fields"""
    identifier = unique_identifier()
    payload = {
        "identifier": identifier,
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["identifier"] == identifier
    assert body["participantCount"] == 2
    assert body["illegalPairCount"] == 0


@pytest.mark.asyncio
async def test_create_group_with_description(client: AsyncClient):
    """Test group creation with optional description"""
    identifier = unique_identifier()
    payload = {
        "identifier": identifier,
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [],
        "description": "A test group with description",
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["identifier"] == identifier


@pytest.mark.asyncio
async def test_create_group_and_reveal(client: AsyncClient):
    """Test full workflow: create group and reveal assignments"""
    identifier = unique_identifier()
    payload = {
        "identifier": identifier,
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
    assert body["identifier"] == identifier
    assert body["participantCount"] == 3
    assert body["illegalPairCount"] == 1

    assignments: Dict[str, str] = {}
    for participant in ["Alice", "Bob", "Charlie"]:
        reveal_response = await client.post(
            f"/api/groups/{identifier}/reveal",
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
    """Test that duplicate identifiers return 409 Conflict"""
    identifier = unique_identifier()
    payload = {
        "identifier": identifier,
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


@pytest.mark.asyncio
async def test_case_insensitive_identifier_conflict(client: AsyncClient):
    """Test that duplicate identifier creation fails even when casing differs in a PascalCase way"""
    # We'll use a fixed identifier to test case-insensitive lookups
    # First create with TestFrostyTree, then try FrostyTreeTest (different casing but still PascalCase)
    identifier1 = unique_identifier()
    payload1 = {
        "identifier": identifier1,
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [],
    }

    first = await client.post("/api/groups", json=payload1)
    assert first.status_code == 201

    # Try with exact same identifier again
    payload2 = {
        "identifier": identifier1,
        "participants": [
            {"name": "Charlie"},
            {"name": "David"},
        ],
        "illegalPairs": [],
    }

    second = await client.post("/api/groups", json=payload2)
    assert second.status_code == 409, f"Expected 409 but got {second.status_code}: {second.text}"


@pytest.mark.asyncio
async def test_invalid_identifier_format(client: AsyncClient):
    """Test that invalid identifier formats are rejected"""
    # Not PascalCase
    payload = {
        "identifier": "invalid_identifier",
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_insufficient_participants(client: AsyncClient):
    """Test that groups require at least 2 participants"""
    payload = {
        "identifier": unique_identifier(),
        "participants": [
            {"name": "Alice"},
        ],
        "illegalPairs": [],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_duplicate_participant_names(client: AsyncClient):
    """Test that duplicate participant names are rejected"""
    payload = {
        "identifier": unique_identifier(),
        "participants": [
            {"name": "Alice"},
            {"name": "Alice"},  # duplicate
        ],
        "illegalPairs": [],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 400
    assert "Duplicate participant name" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_participant_names_case_insensitive(client: AsyncClient):
    """Test that duplicate detection is case-insensitive"""
    payload = {
        "identifier": unique_identifier(),
        "participants": [
            {"name": "Alice"},
            {"name": "ALICE"},  # same name, different case
        ],
        "illegalPairs": [],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 400
    assert "Duplicate participant name" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_constraint_reference(client: AsyncClient):
    """Test that constraints with unknown participants are rejected"""
    payload = {
        "identifier": unique_identifier(),
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [
            {"giver": "Alice", "receiver": "Unknown"}  # Unknown doesn't exist
        ],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 400
    assert "unknown participant" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_self_constraint_not_allowed(client: AsyncClient):
    """Test that self-referential constraints are rejected"""
    payload = {
        "identifier": unique_identifier(),
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [
            {"giver": "Alice", "receiver": "Alice"}  # self-reference
        ],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 422
    assert "different people" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_reveal_nonexistent_group(client: AsyncClient):
    """Test that revealing a match in a nonexistent group returns 404"""
    response = await client.post(
        f"/api/groups/{unique_identifier()}/reveal",
        json={"name": "Alice"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reveal_nonexistent_participant(client: AsyncClient):
    """Test that revealing for a nonexistent participant returns 404"""
    identifier = unique_identifier()
    # First create a group
    payload = {
        "identifier": identifier,
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [],
    }

    create_response = await client.post("/api/groups", json=payload)
    assert create_response.status_code == 201

    # Try to reveal for a participant that doesn't exist
    response = await client.post(
        f"/api/groups/{identifier}/reveal",
        json={"name": "Unknown"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reveal_case_insensitive(client: AsyncClient):
    """Test that participant name matching is case-insensitive"""
    identifier = unique_identifier()
    payload = {
        "identifier": identifier,
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "illegalPairs": [],
    }

    create_response = await client.post("/api/groups", json=payload)
    assert create_response.status_code == 201

    # Reveal with different case
    response = await client.post(
        f"/api/groups/{identifier}/reveal",
        json={"name": "ALICE"},
    )
    assert response.status_code == 200
    assert response.json()["participantName"] == "Alice"


@pytest.mark.asyncio
async def test_large_group(client: AsyncClient):
    """Test group creation with many participants"""
    participants = [{"name": f"Person{i}"} for i in range(20)]

    payload = {
        "identifier": unique_identifier(),
        "participants": participants,
        "illegalPairs": [],
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["participantCount"] == 20


@pytest.mark.asyncio
async def test_many_constraints(client: AsyncClient):
    """Test group with many constraints"""
    participants = [{"name": f"Person{i}"} for i in range(5)]

    # Create constraints between many pairs
    constraints = [
        {"giver": "Person0", "receiver": "Person1"},
        {"giver": "Person0", "receiver": "Person2"},
        {"giver": "Person1", "receiver": "Person2"},
        {"giver": "Person2", "receiver": "Person3"},
        {"giver": "Person3", "receiver": "Person4"},
    ]

    payload = {
        "identifier": unique_identifier(),
        "participants": participants,
        "illegalPairs": constraints,
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["participantCount"] == 5
    assert body["illegalPairCount"] == 5


@pytest.mark.asyncio
async def test_match_validity_no_double_givers(client: AsyncClient):
    """Test that each participant gives exactly once (no double givers)"""
    identifier = unique_identifier()
    participants = [{"name": f"Person{i}"} for i in range(4)]

    payload = {
        "identifier": identifier,
        "participants": participants,
        "illegalPairs": [],
    }

    create_response = await client.post("/api/groups", json=payload)
    assert create_response.status_code == 201

    # Retrieve all matches
    matches = []
    for i in range(4):
        reveal_response = await client.post(
            f"/api/groups/{identifier}/reveal",
            json={"name": f"Person{i}"},
        )
        assert reveal_response.status_code == 200
        matches.append((f"Person{i}", reveal_response.json()["recipientName"]))

    # Verify each person appears as giver exactly once
    givers = [match[0] for match in matches]
    assert len(givers) == len(set(givers)), "Some participants gave multiple times"
    assert set(givers) == {f"Person{i}" for i in range(4)}, "Not all participants are givers"


@pytest.mark.asyncio
async def test_match_validity_no_double_recipients(client: AsyncClient):
    """Test that each participant receives exactly once (no double recipients)"""
    identifier = unique_identifier()
    participants = [{"name": f"Person{i}"} for i in range(4)]

    payload = {
        "identifier": identifier,
        "participants": participants,
        "illegalPairs": [],
    }

    create_response = await client.post("/api/groups", json=payload)
    assert create_response.status_code == 201

    # Retrieve all matches
    matches = []
    for i in range(4):
        reveal_response = await client.post(
            f"/api/groups/{identifier}/reveal",
            json={"name": f"Person{i}"},
        )
        assert reveal_response.status_code == 200
        matches.append((f"Person{i}", reveal_response.json()["recipientName"]))

    # Verify each person appears as recipient exactly once
    recipients = [match[1] for match in matches]
    assert len(recipients) == len(set(recipients)), "Some participants received multiple gifts"
    assert set(recipients) == {f"Person{i}" for i in range(4)}, "Not all participants are recipients"


@pytest.mark.asyncio
async def test_impossible_constraints_rejected(client: AsyncClient):
    """Test that impossible constraint combinations are rejected"""
    participants = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]

    # Make constraints impossible: Alice can't give to Bob or Charlie, so she must give to herself
    constraints = [
        {"giver": "Alice", "receiver": "Bob"},
        {"giver": "Alice", "receiver": "Charlie"},
    ]

    payload = {
        "identifier": unique_identifier(),
        "participants": participants,
        "illegalPairs": constraints,
    }

    response = await client.post("/api/groups", json=payload)
    # Should fail because constraints are impossible to satisfy
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    assert "constraint" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_complex_constraint_chain(client: AsyncClient):
    """Test group with complex overlapping constraints"""
    participants = [{"name": f"Person{i}"} for i in range(6)]

    # Create a complex but solvable constraint pattern
    constraints = [
        {"giver": "Person0", "receiver": "Person1"},
        {"giver": "Person1", "receiver": "Person2"},
        {"giver": "Person2", "receiver": "Person0"},
        {"giver": "Person3", "receiver": "Person4"},
        {"giver": "Person4", "receiver": "Person3"},
    ]

    payload = {
        "identifier": unique_identifier(),
        "participants": participants,
        "illegalPairs": constraints,
    }

    response = await client.post("/api/groups", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["participantCount"] == 6

    # Verify the matches respect all constraints
    matches = {}
    for i in range(6):
        reveal_response = await client.post(
            f"/api/groups/{payload['identifier']}/reveal",
            json={"name": f"Person{i}"},
        )
        assert reveal_response.status_code == 200
        matches[f"Person{i}"] = reveal_response.json()["recipientName"]

    # Check that no forbidden pair exists in the matches
    for constraint in constraints:
        giver = constraint["giver"]
        receiver = constraint["receiver"]
        assert matches[giver] != receiver, f"Constraint violated: {giver} gave to {receiver}"
