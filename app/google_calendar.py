# app/google_calendar.py
import os
from datetime import datetime
from typing import Optional

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import timedelta
import pytz
from .models import Booking, EventType

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
from typing import Any 

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

DEFAULT_TIMEZONE = "Asia/Almaty"


SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_creds_from_user(user: Any) -> Credentials:
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES
    )
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            user.google_access_token = creds.token
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None

    return creds

def get_service(user: Any):
    creds = get_creds_from_user(user)
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)


# Update your create_event function to accept a USER, not read a file
def create_event_for_booking(booking, event_type, user):
    service = get_service(user) # Pass the user object here
    if not service:
        raise Exception("Could not authenticate with Google")
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
def get_busy_intervals(
    start_dt: datetime, 
    end_dt: datetime, 
    calendar_id: str = "primary"
) -> list:
    """
    Fetch 'busy' intervals from Google Calendar between two datetimes.
    """
    service = _get_service()
    
    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": DEFAULT_TIMEZONE, 
        "items": [{"id": calendar_id}]
    }

    events_result = service.freebusy().query(body=body).execute()
    calendars = events_result.get("calendars", {})
    cal_data = calendars.get(calendar_id, {})
    return cal_data.get("busy", [])
def is_overlapping(slot_start: datetime, slot_end: datetime, busy_intervals: list) -> bool:
    """
    Check if a specific time slot overlaps with any busy interval.
    """
    # 1. Ensure slot times are timezone aware (localize to your default settings)
    tz = pytz.timezone(DEFAULT_TIMEZONE)
    if slot_start.tzinfo is None:
        slot_start = tz.localize(slot_start)
    if slot_end.tzinfo is None:
        slot_end = tz.localize(slot_end)

    for interval in busy_intervals:
        # Google returns ISO strings, usually in UTC (Z) or with offset
        # We parse them into datetime objects
        b_start = datetime.fromisoformat(interval["start"].replace("Z", "+00:00"))
        b_end = datetime.fromisoformat(interval["end"].replace("Z", "+00:00"))

        # 2. Check for overlap
        # Logic: (StartA < EndB) and (EndA > StartB)
        if slot_start < b_end and slot_end > b_start:
            return True
            
    return False