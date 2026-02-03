from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base
import datetime

class Court(Base):
    __tablename__ = "courts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    num_courts = Column(Integer, default=1)
    surface = Column(String, nullable=True)
    indoor = Column(Boolean, default=False)
    notes = Column(Text, default="")
    hours = Column(String, nullable=True)  # store hours/schedule like "Mon-Fri 07:00-21:00"

    visits = relationship("Visit", back_populates="court", cascade="all, delete-orphan")

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    court_id = Column(Integer, ForeignKey("courts.id", ondelete="CASCADE"), nullable=False)
    visited_at = Column(DateTime, default=datetime.datetime.utcnow)
    crowdedness = Column(Integer, nullable=True)
    notes = Column(Text, default="")

    court = relationship("Court", back_populates="visits")