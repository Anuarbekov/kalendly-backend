# app/google_calendar.py
import os
from datetime import datetime
from typing import Optional

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .models import Booking, EventType

# Same scope as in google_auth_setup.py
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Change this to your timezone if you want (right now it's Almaty)
DEFAULT_TIMEZONE = "Asia/Almaty"


def _get_creds() -> Credentials:
    """
    Load credentials from token.json and refresh if needed.
    Assumes token.json is in the backend root directory.
    """
    token_path = os.path.join(os.path.dirname(__file__), "..", "token.json")
    token_path = os.path.abspath(token_path)

    if not os.path.exists(token_path):
        raise RuntimeError("token.json not found. Run google_auth_setup.py first.")

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # save refreshed token
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def _get_service():
    creds = _get_creds()
    service = build("calendar", "v3", credentials=creds)
    return service


def create_event_for_booking(
    booking: Booking,
    event_type: EventType,
    calendar_id: str = "primary",
    timezone: str = DEFAULT_TIMEZONE,
) -> str:
    """
    Create a Google Calendar event for given booking.
    Returns the Google event id.
    """
    service = _get_service()

    # ensure datetimes are ISO formatted strings
    start_iso = booking.start_datetime.isoformat()
    end_iso = booking.end_datetime.isoformat()

    summary = f"{event_type.name} – {booking.invitee_name}"
    description_parts = []
    if booking.invitee_note:
        description_parts.append(f"Note from invitee: {booking.invitee_note}")
    description_parts.append(f"Event type: {event_type.name}")
    description = "\n".join(description_parts)

    event_body = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_iso,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": timezone,
        },
        "attendees": [
            {"email": booking.invitee_email},
            # you can also add your own email here if you want explicit invite
            # {"email": "your_email@gmail.com"}
        ],
    }

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    return event.get("id")
