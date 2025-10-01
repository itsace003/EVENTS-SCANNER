from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    date_time = Column(DateTime, nullable=False, index=True)
    location = Column(String)
    source_url = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # 'luma' or 'meetup'
    category = Column(String, index=True)
    ai_relevance_score = Column(Integer, default=0)  # 1-10 scale
    tags = Column(JSON, default=list)
    organizer = Column(String)
    event_type = Column(String)  # 'online', 'in-person', 'hybrid'
    price = Column(Float, default=0.0)
    max_attendees = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to watched events
    watched_by = relationship("WatchedEvent", back_populates="event")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    session_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSON, default=dict)  # location, categories, etc.
    location = Column(String)  # User's preferred location
    
    # Relationship to watched events
    watched_events = relationship("WatchedEvent", back_populates="session")

class WatchedEvent(Base):
    __tablename__ = "watched_events"
    
    session_id = Column(String, ForeignKey("user_sessions.session_id"), primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), primary_key=True)
    watched_at = Column(DateTime, default=datetime.utcnow)
    rating = Column(Integer)  # Optional: user can rate the event
    notes = Column(Text)  # Optional: user notes
    
    # Relationships
    session = relationship("UserSession", back_populates="watched_events")
    event = relationship("Event", back_populates="watched_by")

class EventDiscoveryLog(Base):
    __tablename__ = "event_discovery_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    search_query = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    location = Column(String)
    events_found = Column(Integer, default=0)
    events_classified = Column(Integer, default=0)
    execution_time = Column(Float)  # in seconds
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class APIUsageLog(Base):
    __tablename__ = "api_usage_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(String, nullable=False)
    session_id = Column(String)
    request_data = Column(JSON)
    response_status = Column(Integer)
    response_time = Column(Float)  # in milliseconds
    timestamp = Column(DateTime, default=datetime.utcnow)