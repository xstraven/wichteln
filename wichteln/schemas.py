from pydantic import BaseModel, validator, constr, Field
from typing import List, Optional
import re


class ParticipantInput(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)


class IllegalPairInput(BaseModel):
    giver: constr(strip_whitespace=True, min_length=1)
    receiver: constr(strip_whitespace=True, min_length=1)

    @validator("receiver")
    def giver_cannot_equal_receiver(cls, receiver: str, values) -> str:
        giver = values.get("giver", "").strip().lower()
        if giver and giver == receiver.strip().lower():
            raise ValueError("Giver and receiver in an illegal pair must be different people")
        return receiver


PASCAL_THREE_WORDS = re.compile(r"^[A-Z][a-z]+(?:[A-Z][a-z]+){2,}$")


class GroupCreateRequest(BaseModel):
    identifier: constr(strip_whitespace=True, min_length=6, max_length=80)
    participants: List[ParticipantInput]
    illegalPairs: List[IllegalPairInput] = Field(default_factory=list)
    description: Optional[constr(max_length=500)] = None

    @validator("identifier")
    def identifier_must_be_camel_case_three_words(cls, value: str) -> str:
        if not PASCAL_THREE_WORDS.match(value):
            raise ValueError(
                "Identifier must be three or more words in PascalCase (e.g. SnowyLittleReindeer)"
            )
        return value

    @validator("participants")
    def require_at_least_two_participants(cls, participants: List[ParticipantInput]) -> List[ParticipantInput]:
        if len(participants) < 2:
            raise ValueError("At least two participants are required")
        return participants


class GroupCreateResponse(BaseModel):
    identifier: str
    participantCount: int
    illegalPairCount: int


class RevealRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)


class RevealResponse(BaseModel):
    identifier: str
    participantName: str
    recipientName: str


class HealthResponse(BaseModel):
    status: str


class IdentifierResponse(BaseModel):
    identifier: str
