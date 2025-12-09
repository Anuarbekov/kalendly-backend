
from fastapi import APIRouter, Depends, HTTPException, Query
import pytz
from sqlalchemy.orm import Session
from datetime import datetime, time, timedelta, date
from typing import List
from ..db import get_db
from .. import schemas, crud, models
from ..services.google_calendar import create_event_for_booking,get_busy_intervals, is_overlapping, DEFAULT_TIMEZONE

router = APIRouter(prefix="/public", tags=["public"])


def _parse_time_str(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(hour=h, minute=m)


def _generate_slots_for_date(
    event_type: models.EventType, rules: List[models.AvailabilityRule], day: date
) -> List[schemas.TimeSlot]:
    slots: List[schemas.TimeSlot] = []
    duration = timedelta(minutes=event_type.duration_minutes)
    buffer = timedelta(minutes=event_type.buffer_minutes)

    for rule in rules:
        start_t = _parse_time_str(rule.start_time)
        end_t = _parse_time_str(rule.end_time)

        current = datetime.combine(day, start_t)
        end_dt = datetime.combine(day, end_t)

        while current + duration <= end_dt:
            slot_start = current
            slot_end = current + duration
            slots.append(
                schemas.TimeSlot(start=slot_start, end=slot_end)
            )
            current = slot_end + buffer

    return slots


@router.get("/{slug}/details", response_model=schemas.PublicEventTypeRead)
def get_public_event_type(slug: str, db: Session = Depends(get_db)):
    et = crud.get_event_type_by_slug(db, slug)
    if not et or not et.is_active:
        raise HTTPException(status_code=404, detail="Event type not found")
    
    return schemas.PublicEventTypeRead(
        name=et.name,
        slug=et.slug,
        duration_minutes=et.duration_minutes,
        location_type=et.location_type,
        host_name=et.owner.email
    )


@router.get("/{slug}/slots", response_model=List[schemas.TimeSlot])
def get_slots_for_date(
    slug: str,
    date_str: str = Query(..., alias="date"),
    db: Session = Depends(get_db),
):
    et = crud.get_event_type_by_slug(db, slug)
    if not et or not et.is_active:
        raise HTTPException(status_code=404, detail="Event type not found")

    try:
        day = datetime.fromisoformat(date_str).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
        
    weekday = day.weekday()
    rules = [r for r in et.availability_rules if r.weekday == weekday]
    possible_slots = _generate_slots_for_date(et, rules, day)

    if not possible_slots:
        return []

    tz = pytz.timezone(DEFAULT_TIMEZONE)
    
    start_of_day = datetime.combine(day, time.min)
    start_of_day = tz.localize(start_of_day)
    
    end_of_day = datetime.combine(day, time.max)
    end_of_day = tz.localize(end_of_day)

    try:
        busy_times = get_busy_intervals(et.owner, start_of_day, end_of_day)
    except Exception as e:
        print(f"Google Calendar Error: {e}")
        busy_times = []

    final_slots = []
    for slot in possible_slots:
        if not is_overlapping(slot.start, slot.end, busy_times):
            final_slots.append(slot)

    return final_slots

@router.post("/{slug}/book", response_model=schemas.BookingRead)
def book_slot(
    slug: str,
    data: schemas.BookingCreate,
    db: Session = Depends(get_db),
):
    et = crud.get_event_type_by_slug(db, slug)
    if not et or not et.is_active:
        raise HTTPException(status_code=404, detail="Event type not found")

    booking = crud.create_booking(db, et, data)
    if not booking:
        raise HTTPException(status_code=500, detail="Internal Server Error: Booking creation failed")

    booking.status = "pending"
    db.commit()      # Save pending state
    db.refresh(booking)
    try:
        event_id = create_event_for_booking(booking, et)
        booking.gcal_event_id = event_id
        db.add(booking)
        db.commit()  # Update with GCal ID
        db.refresh(booking)
    except Exception as e:
        # If Google fails, we log it, but the USER still gets their booking confirmation
        print(f"WARNING: Failed to create Google Calendar event: {e}")
        # Optional: You could append a warning note to the response if your schema allows it
   
    return booking

