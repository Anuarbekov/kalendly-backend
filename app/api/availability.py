from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import schemas, crud, models

router = APIRouter(prefix="/event-types", tags=["availability"])


@router.post("/{event_type_id}/availability", response_model=List[schemas.AvailabilityRuleRead])
def set_availability(
    event_type_id: int,
    rules: List[schemas.AvailabilityRuleCreate],
    db: Session = Depends(get_db),
):
    et = crud.get_event_type(db, event_type_id)
    if not et:
        raise HTTPException(status_code=404, detail="Event type not found")
    new_rules = crud.set_availability_rules(db, et, rules)
    return new_rules

@router.patch("/{event_type_id}/availability", response_model=List[schemas.AvailabilityRuleRead])
def update_availability(
    event_type_id: int,
    rules: List[schemas.AvailabilityRuleCreate],
    db: Session = Depends(get_db),
):
    et = crud.get_event_type(db, event_type_id)
    if not et:
        raise HTTPException(status_code=404, detail="Event type not found")
    print(rules)
    updated_rules = crud.update_availability_rules(db, et, rules)
    return updated_rules