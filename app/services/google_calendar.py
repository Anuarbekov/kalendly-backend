import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import pytz

DEFAULT_TIMEZONE = "Asia/Almaty"
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_google_service(user):
    """
    Reconstructs the Google Credentials object for the given user
    and returns the Calendar Service.
    """
    if not user.google_access_token:
        raise Exception("User is not connected to Google Calendar")

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES
    )
    
    return build('calendar', 'v3', credentials=creds)

def get_busy_intervals(user, start_dt: datetime, end_dt: datetime):
    """
    Fetches 'busy' periods from the user's primary calendar 
    between start_dt and end_dt.
    """
    try:
        service = get_google_service(user)
        
        body = {
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "timeZone": DEFAULT_TIMEZONE,
            "items": [{"id": "primary"}]
        }
        
        events_result = service.freebusy().query(body=body).execute()
        calendars = events_result.get('calendars', {})
        primary_cal = calendars.get('primary', {})
        busy = primary_cal.get('busy', [])
        
        cleaned_busy = []
        for interval in busy:
            cleaned_busy.append({
                'start': datetime.fromisoformat(interval['start']),
                'end': datetime.fromisoformat(interval['end'])
            })
        return cleaned_busy

    except Exception as e:
        print(f"Error fetching busy intervals: {e}")
        return []

def is_overlapping(slot_start: datetime, slot_end: datetime, busy_times: list) -> bool:
    """
    Checks if a specific slot overlaps with any busy interval.
    Handles timezone naive/aware comparison.
    """
    tz = pytz.timezone(DEFAULT_TIMEZONE)
    if slot_start.tzinfo is None:
        slot_start = tz.localize(slot_start)
    if slot_end.tzinfo is None:
        slot_end = tz.localize(slot_end)

    for busy in busy_times:
        b_start = busy['start']
        b_end = busy['end']
        
        if slot_start < b_end and slot_end > b_start:
            return True
            
    return False

def create_event_for_booking(booking, event_type):
    print(event_type)
    host = event_type.owner 
    
    service = get_google_service(host)

    event_body = {
        'summary': f"{event_type.title} with {booking.invitee_name}",
        'description': f"Notes: {booking.invitee_note}",
        'start': {
            'dateTime': booking.start_time.isoformat(),
            'timeZone': DEFAULT_TIMEZONE,
        },
        'end': {
            'dateTime': booking.end_time.isoformat(),
            'timeZone': DEFAULT_TIMEZONE,
        },
        'attendees': [
            {'email': booking.invitee_email},
            {'email': host.email}, 
        ],
        'conferenceData': {
            'createRequest': {
                'requestId': f"meet-{booking.id}", 
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        },
    }

    event = service.events().insert(
        calendarId='primary',
        body=event_body,
        conferenceDataVersion=1,
        sendUpdates='all'
    ).execute()

    return event.get('id')
    