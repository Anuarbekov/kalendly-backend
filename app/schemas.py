
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ---------- Availability ----------
class AvailabilityRuleBase(BaseModel):
    weekday: int  # 0-6
    start_time: str  # "HH:MM"
    end_time: str


class AvailabilityRuleCreate(AvailabilityRuleBase):
    pass


class AvailabilityRuleRead(AvailabilityRuleBase):
    id: int

    class Config:
        orm_mode = True


# ---------- EventType ----------
class EventTypeBase(BaseModel):
    name: str
    slug: str
    duration_minutes: int
    location_type: str = "online"
    location_value: Optional[str] = None
    min_notice_minutes: int = 60
    buffer_minutes: int = 0
    is_active: bool = True


class EventTypeCreate(EventTypeBase):
    pass


class EventTypeUpdate(BaseModel):
    name: Optional[str] = None
    duration_minutes: Optional[int] = None
    location_type: Optional[str] = None
    location_value: Optional[str] = None
    min_notice_minutes: Optional[int] = None
    buffer_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class EventTypeRead(EventTypeBase):
    id: int
    availability_rules: List[AvailabilityRuleRead] = []

    class Config:
        orm_mode = True


# ---------- Booking ----------
class BookingBase(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    invitee_name: str
    invitee_email: EmailStr
    invitee_note: Optional[str] = None


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    status: str
    gcal_event_id: Optional[str] = None

    class Config:
        orm_mode = True
    


# ---------- Public API ----------
class PublicEventTypeRead(BaseModel):
    name: str
    slug: str
    duration_minutes: int
    location_type: str
    host_name: str
    class Config:
        orm_mode = True


class TimeSlot(BaseModel):
    start: datetime
    end: datetime
