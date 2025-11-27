
from fastapi import FastAPI
from .db import Base, engine
from .api import event_types, availability, public
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kalendly Backend")

app.include_router(event_types.router)
app.include_router(availability.router)
app.include_router(public.router)


@app.get("/")
def root():
    return {"status": "ok"}
