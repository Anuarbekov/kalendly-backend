
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .db import Base


class EventType(Base):
    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    location_type = Column(String, default="online")
    location_value = Column(String, nullable=True)
    min_notice_minutes = Column(Integer, default=60)
    buffer_minutes = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="event_types")
    availability_rules = relationship(
        "AvailabilityRule", back_populates="event_type", cascade="all, delete-orphan"
    )
    bookings = relationship("Booking", back_populates="event_type")


class AvailabilityRule(Base):
    __tablename__ = "availability_rules"

    id = Column(Integer, primary_key=True, index=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_time = Column(String, nullable=False)  # "10:00"
    end_time = Column(String, nullable=False)    # "13:00"

    event_type = relationship("EventType", back_populates="availability_rules")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    invitee_name = Column(String, nullable=False)
    invitee_email = Column(String, nullable=False)
    invitee_note = Column(String, nullable=True)
    status = Column(String, default="confirmed")
    gcal_event_id = Column(String, nullable=True)
    event_type = relationship("EventType", back_populates="bookings")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    event_types = relationship("EventType", back_populates="owner")