from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .db import Base, engine
from .api import event_types, availability, public, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kalendly Backend")
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000", # Create React App default
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Allows requests from these URLs
    allow_credentials=True,      # Allows cookies/auth headers
    allow_methods=["*"],         # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],         # Allows all headers
)

app.include_router(auth.router)

app.include_router(event_types.router)
app.include_router(availability.router)
app.include_router(public.router)


@app.get("/")
def root():
    return {"status": "ok"}
