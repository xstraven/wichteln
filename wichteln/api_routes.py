from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
from datetime import datetime

from wichteln.database import get_db
from wichteln.models import SecretSanta
from wichteln.schemas import (
    GroupCreateRequest,
    GroupCreateResponse,
    HealthResponse,
    RevealRequest,
    RevealResponse,
)
from wichteln.utils import generate_secret_santa_matches, slugify

api_router = APIRouter(prefix="/api", tags=["api"])


def _normalise_name(value: str) -> str:
    return value.strip().lower()


@api_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@api_router.post(
    "/groups",
    response_model=GroupCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    payload: GroupCreateRequest, db: AsyncSession = Depends(get_db)
) -> GroupCreateResponse:
    identifier_key = payload.identifier.strip()

    # Check if identifier already exists (case-insensitive)
    result = await db.execute(
        select(SecretSanta).where(func.lower(SecretSanta.human_id) == identifier_key.lower())
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identifier already exists. Please choose a different one.",
        )

    # Check for duplicate participant names
    seen_names = set()
    for participant in payload.participants:
        normalised = _normalise_name(participant.name)
        if normalised in seen_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate participant name detected: {participant.name}",
            )
        seen_names.add(normalised)

    # Create participant records
    participants_data = []
    name_to_participant = {}
    for participant_input in payload.participants:
        participant_name = participant_input.name.strip()
        participants_data.append(participant_name)
        name_to_participant[_normalise_name(participant_name)] = participant_name

    # Process constraints
    constraints_data = []
    constraint_count = 0
    constraints_map: Dict[int, List[int]] = {}

    for pair in payload.illegalPairs:
        giver_key = _normalise_name(pair.giver)
        receiver_key = _normalise_name(pair.receiver)

        if giver_key not in name_to_participant or receiver_key not in name_to_participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Constraint references unknown participant: {pair.giver} → {pair.receiver}",
            )

        # Store constraint with participant names for reference
        constraints_data.append({
            "giver": pair.giver.strip(),
            "receiver": pair.receiver.strip(),
        })
        constraint_count += 1

    # Generate matches using participant indices as IDs
    participant_indices = list(range(len(participants_data)))

    # Build constraints map using indices
    for constraint in constraints_data:
        giver_idx = next(i for i, p in enumerate(participants_data) if _normalise_name(p) == _normalise_name(constraint["giver"]))
        receiver_idx = next(i for i, p in enumerate(participants_data) if _normalise_name(p) == _normalise_name(constraint["receiver"]))
        constraints_map.setdefault(giver_idx, []).append(receiver_idx)

    try:
        matches_dict = generate_secret_santa_matches(participant_indices, constraints_map)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    # Convert matches dict to list format with participant names
    matches_data = []
    for giver_idx, receiver_idx in matches_dict.items():
        matches_data.append({
            "giver": participants_data[giver_idx],
            "receiver": participants_data[receiver_idx],
        })

    # Create the exchange record
    secret_santa = SecretSanta(
        human_id=identifier_key,
        santa={
            "participants": participants_data,
            "constraints": constraints_data,
            "matches": matches_data,
            "description": payload.description,
        },
        created_at=datetime.utcnow(),
    )
    db.add(secret_santa)
    await db.commit()

    return GroupCreateResponse(
        identifier=secret_santa.human_id,
        participantCount=len(participants_data),
        illegalPairCount=constraint_count,
    )


@api_router.post(
    "/groups/{identifier}/reveal",
    response_model=RevealResponse,
)
async def reveal_recipient(
    identifier: str, payload: RevealRequest, db: AsyncSession = Depends(get_db)
) -> RevealResponse:
    # Find the exchange by identifier (case-insensitive)
    result = await db.execute(
        select(SecretSanta).where(func.lower(SecretSanta.human_id) == identifier.lower())
    )
    exchange = result.scalar_one_or_none()
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found."
        )

    # Validate that santa data exists
    if not exchange.santa or "participants" not in exchange.santa or "matches" not in exchange.santa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange data is incomplete.",
        )

    # Find the participant by name (case-insensitive)
    participant_name = payload.name.strip()
    participant_found = None
    for p in exchange.santa["participants"]:
        if _normalise_name(p) == _normalise_name(participant_name):
            participant_found = p
            break

    if not participant_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found in this group.",
        )

    # Find the match for this participant
    recipient_name = None
    for match in exchange.santa["matches"]:
        if _normalise_name(match["giver"]) == _normalise_name(participant_name):
            recipient_name = match["receiver"]
            break

    if not recipient_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matches have not been generated yet.",
        )

    # Update looked_at timestamp
    exchange.looked_at = datetime.utcnow()
    await db.commit()

    return RevealResponse(
        identifier=exchange.human_id,
        participantName=participant_found,
        recipientName=recipient_name,
    )
