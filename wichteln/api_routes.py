from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from wichteln.database import get_db
from wichteln.models import Constraint, Exchange, Match, Participant
from wichteln.schemas import (
    GroupCreateRequest,
    GroupCreateResponse,
    HealthResponse,
    RevealRequest,
    RevealResponse,
)
from wichteln.utils import generate_secret_santa_matches, generate_unique_code, slugify

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

    result = await db.execute(
        select(Exchange).where(func.lower(Exchange.identifier) == identifier_key.lower())
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identifier already exists. Please choose a different one.",
        )

    seen_names = set()
    for participant in payload.participants:
        normalised = _normalise_name(participant.name)
        if normalised in seen_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate participant name detected: {participant.name}",
            )
        seen_names.add(normalised)

    exchange = Exchange(
        name=payload.description or identifier_key,
        identifier=identifier_key,
        description=payload.description,
        is_completed=False,
    )
    db.add(exchange)
    await db.flush()

    identifier_slug = slugify(identifier_key)
    email_local_counts: Dict[str, int] = {}
    participant_records: List[Participant] = []
    for participant_input in payload.participants:
        base_local = slugify(participant_input.name) or "participant"
        email_local_counts.setdefault(base_local, 0)
        email_local_counts[base_local] += 1
        local_part = (
            base_local
            if email_local_counts[base_local] == 1
            else f"{base_local}{email_local_counts[base_local]}"
        )
        email = f"{local_part}@{identifier_slug}.invalid"

        participant = Participant(
            name=participant_input.name.strip(),
            email=email,
            code=generate_unique_code(),
            exchange_id=exchange.id,
        )
        db.add(participant)
        participant_records.append(participant)

    await db.flush()

    name_to_participant = {
        _normalise_name(participant.name): participant
        for participant in participant_records
    }

    constraints_map: Dict[int, List[int]] = {}
    constraint_count = 0

    for pair in payload.illegalPairs:
        giver = name_to_participant.get(_normalise_name(pair.giver))
        receiver = name_to_participant.get(_normalise_name(pair.receiver))
        if not giver or not receiver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Constraint references unknown participant: {pair.giver} → {pair.receiver}",
            )
        constraint = Constraint(
            participant_id=giver.id, excluded_participant_id=receiver.id
        )
        db.add(constraint)
        constraint_count += 1
        constraints_map.setdefault(giver.id, []).append(receiver.id)

    participant_ids = [participant.id for participant in participant_records]

    try:
        matches = generate_secret_santa_matches(participant_ids, constraints_map)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    for giver_id, receiver_id in matches.items():
        db.add(
            Match(exchange_id=exchange.id, giver_id=giver_id, receiver_id=receiver_id)
        )

    exchange.is_completed = True
    await db.commit()

    return GroupCreateResponse(
        identifier=exchange.identifier,
        participantCount=len(participant_records),
        illegalPairCount=constraint_count,
    )


@api_router.post(
    "/groups/{identifier}/reveal",
    response_model=RevealResponse,
)
async def reveal_recipient(
    identifier: str, payload: RevealRequest, db: AsyncSession = Depends(get_db)
) -> RevealResponse:
    result = await db.execute(
        select(Exchange).where(func.lower(Exchange.identifier) == identifier.lower())
    )
    exchange = result.scalar_one_or_none()
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found."
        )

    participant_result = await db.execute(
        select(Participant).where(
            Participant.exchange_id == exchange.id,
            func.lower(Participant.name) == _normalise_name(payload.name),
        )
    )
    participant = participant_result.scalar_one_or_none()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found in this group.",
        )

    match_result = await db.execute(
        select(Match).where(
            Match.exchange_id == exchange.id, Match.giver_id == participant.id
        )
    )
    match = match_result.scalar_one_or_none()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matches have not been generated yet.",
        )

    receiver_result = await db.execute(
        select(Participant).where(Participant.id == match.receiver_id)
    )
    receiver = receiver_result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match data incomplete. Please regenerate the group.",
        )

    return RevealResponse(
        identifier=exchange.identifier,
        participantName=participant.name,
        recipientName=receiver.name,
    )
