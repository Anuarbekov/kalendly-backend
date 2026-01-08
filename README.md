# Kalendly

FastAPI server for scheduling logic and Google Calendar integration.

## 🛠 Tech Stack
* **Framework:** FastAPI (Python)
* **ORM:** SQLAlchemy
* **Auth:** Google OAuth2
* **Integration:** Google Calendar API

## 🚀 Features
* **Calendar Sync:** Conflict checking and Google Meet generation.
* **Availability Engine:** Weekday-based rule validation.
* **Database:** Cascade deletions and partial (PATCH) updates.
* **Security:** JWT/OAuth dependency injection.

## 📂 Structure
* `api/`: Endpoint routers (Auth, Event Types, Bookings).
* `services/`: Google Calendar API logic.
* `models.py`: SQLAlchemy tables (EventType, Booking, User).
* `schemas.py`: Pydantic validation models.
* `crud.py`: Database operations.

## ⚙️ Setup
1. `pip install -r requirements.txt`
2. Configure Google Cloud Console (OAuth & Calendar API).
3. Set environment variables for Database and Google Credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY).
4. `uvicorn main:app --reload`

## 📄 License
Educational Use.
