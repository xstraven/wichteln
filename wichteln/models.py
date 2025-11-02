from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from typing import Optional

Base = declarative_base()


class SecretSanta(Base):
    """
    Simplified single-table schema for secret santa exchanges.
    All exchange data (participants, constraints, matches) stored as JSON.
    """
    __tablename__ = "secret_santa"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    human_id = Column(String, unique=True, nullable=False, index=True)  # e.g., "CozyPineMittens"
    santa = Column(JSON, nullable=True)  # Stores: {participants, constraints, matches, description}
    created_at = Column(DateTime, default=datetime.utcnow)
    looked_at = Column(DateTime, nullable=True)
