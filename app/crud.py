
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models, schemas


# ---------- EventType ----------
def create_event_type(db: Session, data: schemas.EventTypeCreate) -> models.EventType:
    et = models.EventType(**data.dict())
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


def get_event_types(db: Session) -> List[models.EventType]:
    return db.query(models.EventType).all()


def get_event_type_by_slug(db: Session, slug: str) -> Optional[models.EventType]:
    return db.query(models.EventType).filter(models.EventType.slug == slug).first()


def get_event_type(db: Session, event_type_id: int) -> Optional[models.EventType]:
    return db.query(models.EventType).filter(models.EventType.id == event_type_id).first()


def update_event_type(
    db: Session, event_type: models.EventType, data: schemas.EventTypeUpdate
) -> models.EventType:
    for field, value in data.dict(exclude_unset=True).items():
        setattr(event_type, field, value)
    db.commit()
    db.refresh(event_type)
    return event_type


def delete_event_type(db: Session, event_type: models.EventType):
    db.delete(event_type)
    db.commit()


# ---------- Availability ----------
def set_availability_rules(
    db: Session,
    event_type: models.EventType,
    rules: List[schemas.AvailabilityRuleCreate],
) -> List[models.AvailabilityRule]:
    # delete existing
    for r in list(event_type.availability_rules):
        db.delete(r)
    db.flush()

    new_rules = []
    for r in rules:
        rule = models.AvailabilityRule(
            event_type_id=event_type.id, **r.dict()
        )
        db.add(rule)
        new_rules.append(rule)

    db.commit()
    for r in new_rules:
        db.refresh(r)
    return new_rules


# ---------- Booking ----------
def create_booking(
    db: Session,
    event_type: models.EventType,
    data: schemas.BookingCreate,
) -> models.Booking:
    booking = models.Booking(
        event_type_id=event_type.id,
        **data.dict(),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
