
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.auth import get_current_user

from ..db import get_db
from .. import schemas, crud, models


router = APIRouter(prefix="/event-types", tags=["event-types"])


@router.post("/", response_model=schemas.EventTypeRead)
def create_event_type(
    event: schemas.EventTypeCreate, db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)
):
    return crud.create_event_type(db, event, user_id=current_user.id)


@router.get("/", response_model=List[schemas.EventTypeRead])
def list_event_types(db: Session = Depends(get_db)):
    return crud.get_event_types(db)


@router.get("/{event_type_id}", response_model=schemas.EventTypeRead)
def get_event_type(event_type_id: int, db: Session = Depends(get_db)):
    et = crud.get_event_type(db, event_type_id)
    if not et:
        raise HTTPException(status_code=404, detail="Event type not found")
    return et


@router.put("/{event_type_id}", response_model=schemas.EventTypeRead)
def update_event_type(
    event_type_id: int,
    data: schemas.EventTypeUpdate,
    db: Session = Depends(get_db),
):
    et = crud.get_event_type(db, event_type_id)
    if not et:
        raise HTTPException(status_code=404, detail="Event type not found")
    return crud.update_event_type(db, et, data)

@router.patch("/{event_type_id}", response_model=schemas.EventTypeRead)
def patch_event_type(
    event_type_id: int,
    data: dict, # Using dict to accept partial updates dynamically
    db: Session = Depends(get_db),
):
    et = crud.get_event_type(db, event_type_id)
    if not et:
        raise HTTPException(status_code=404, detail="Event type not found")
    
    # Update only the fields provided in the request body
    for key, value in data.items():
        if hasattr(et, key):
            setattr(et, key, value)
            
    db.commit()
    db.refresh(et)
    return et

@router.delete("/{event_type_id}")
def delete_event_type(event_type_id: int, db: Session = Depends(get_db)):
    et = crud.get_event_type(db, event_type_id)
    if not et:
        raise HTTPException(status_code=404, detail="Event type not found")
    crud.delete_event_type(db, et)
    return {"ok": True}
