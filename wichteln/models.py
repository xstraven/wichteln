from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Exchange(Base):
    __tablename__ = "exchanges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    
    participants = relationship("Participant", back_populates="exchange")
    matches = relationship("Match", back_populates="exchange")

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"))
    
    exchange = relationship("Exchange", back_populates="participants")
    constraints = relationship("Constraint", foreign_keys="Constraint.participant_id", back_populates="participant")
    excluded_by = relationship("Constraint", foreign_keys="Constraint.excluded_participant_id", back_populates="excluded_participant")

class Constraint(Base):
    __tablename__ = "constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"))
    excluded_participant_id = Column(Integer, ForeignKey("participants.id"))
    
    participant = relationship("Participant", foreign_keys=[participant_id], back_populates="constraints")
    excluded_participant = relationship("Participant", foreign_keys=[excluded_participant_id], back_populates="excluded_by")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"))
    giver_id = Column(Integer, ForeignKey("participants.id"))
    receiver_id = Column(Integer, ForeignKey("participants.id"))
    
    exchange = relationship("Exchange", back_populates="matches")
    giver = relationship("Participant", foreign_keys=[giver_id])
    receiver = relationship("Participant", foreign_keys=[receiver_id])