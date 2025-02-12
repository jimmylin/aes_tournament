import requests
import json
import gspread
import sys
import urllib.parse
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Google API Scopes
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "credentials.json"
CALENDAR_ID = "c_0eef2fb98021a9aef935dc75c856cb8501e878668c1b372de04b463570877913@group.calendar.google.com"  # Replace with your Google Calendar ID

def fetch_aes_data(tournament_id):
    url = f"https://www.advancedeventsystems.com/api/landing/events/{tournament_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Data fetched for tournament {tournament_id}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for tournament {tournament_id}: {e}")
        return None

def format_date(date_str):
    """Convert ISO date to 'Mon Day, Year' with correct suffix."""
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", ""))
            day = dt.day
            suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            return dt.strftime(f"%b {day}{suffix}, %Y")  # Example: "Jan 1st, 2025"
        except ValueError:
            return date_str
    return ""

def format_date_google(date_str):
    """Convert ISO date to Google Calendar format (YYYY-MM-DD)."""
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", ""))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None

def load_existing_data(sheet):
    """Load existing tournament data from Google Sheets."""
    data = sheet.get_all_values()
    if not data:
        return {}, []

    headers = data[0]
    rows = data[1:]

    existing_tournaments = {}
    for row in rows:
        event_id = row[0].split('"')[3] if "HYPERLINK" in row[0] else row[0]
        existing_tournaments[event_id] = row

    return existing_tournaments, headers

def authenticate_google_calendar():
    """Authenticate and return a Google Calendar service."""
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("calendar", "v3", credentials=credentials)
    return service

def event_exists(service, event_id):
    """Check if an event with the given AES event ID already exists in Google Calendar."""
    events_result = service.events().list(calendarId=CALENDAR_ID).execute()
    for event in events_result.get("items", []):
        if event.get("description", "").startswith(f"AES Event ID: {event_id}"):
            return True
    return False

def create_google_calendar_event(service, data):
    """Create a Google Calendar event for the tournament."""
    event_id = str(data.get("eventId"))
    event_name = data.get("name")
    
    start_date = format_date_google(data.get("startDate"))
    end_date = format_date_google(data.get("endDate"))

    if not start_date or not end_date:
        print(f"❌ Skipping event {event_name}: Invalid dates")
        return
    
    end_date_plus_one = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    address_parts = [
        data.get('address', {}).get('line1', ''),
        data.get('address', {}).get('city', ''),
        data.get('address', {}).get('state', {}).get('abbreviation', ''),
        data.get('address', {}).get('zip', '')
    ]
    full_address = ", ".join(filter(None, address_parts))
    maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(full_address)}"
    aes_url = f"https://www.advancedeventsystems.com/events/{event_id}"

    event_details = f"""
    **{event_name}**
    Location: {full_address}
    AES Link: {aes_url}
    Google Maps: {maps_url}

    AES Event ID: {event_id}
    """

    if event_exists(service, event_id):
        print(f"⚠️ Event {event_name} already exists in Google Calendar. Skipping...")
        return

    event = {
        "summary": event_name,
        "location": full_address,
        "description": event_details,
        "start": {"date": start_date},
        "end": {"date": end_date_plus_one},  # Google Calendar needs exclusive end date
    }

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"✅ Created event in Google Calendar: {event_name}")

def write_to_google_sheets(sheet_name, tournament_list):
    """Write tournament data to Google Sheets."""
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1

    existing_tournaments, headers = load_existing_data(sheet)

    readable_headers = [
        "AES Link", "Tournament Name", "Location", 
        "Start Date", "End Date", 
        "Reg Opens", "Reg Closes", "Late Reg", "USAV Sanctioned"
    ]

    if not headers or headers != readable_headers:
        sheet.clear()
        sheet.append_row(readable_headers)

    updated_rows = []
    for data in tournament_list:
        event_id = str(data.get("eventId"))
        aes_url = f"https://www.advancedeventsystems.com/events/{event_id}"
        event_id_hyperlink = f'=HYPERLINK("{aes_url}", "{event_id}")'

        name_hyperlink = f'=HYPERLINK("{data.get("website")}", "{data.get("name")}")' if data.get("website") else data.get("name")

        address_parts = [
            data.get('address', {}).get('line1', ''),
            data.get('address', {}).get('city', ''),
            data.get('address', {}).get('state', {}).get('abbreviation', ''),
            data.get('address', {}).get('zip', '')
        ]
        full_address = ", ".join(filter(None, address_parts))
        maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(full_address)}"
        location_hyperlink = f'=HYPERLINK("{maps_url}", "{data.get("locationName")}")' if full_address else data.get("locationName")

        row = [
            event_id_hyperlink,
            name_hyperlink,
            location_hyperlink,
            format_date(data.get("startDate")),
            format_date(data.get("endDate")),
            format_date(data.get("registrationOpenDate")),
            format_date(data.get("registrationCloseDate")),
            format_date(data.get("lateRegistrationDate")),
            data.get("affiliation", {}).get("isUSAV")
        ]

        if event_id in existing_tournaments:
            existing_tournaments[event_id] = row
        else:
            updated_rows.append(row)

    sheet.clear()
    sheet.append_row(readable_headers)
    for row in existing_tournaments.values():
        sheet.append_row(row, value_input_option="USER_ENTERED")
    for row in updated_rows:
        sheet.append_row(row, value_input_option="USER_ENTERED")

    print(f"✅ Data successfully written to Google Sheets: {sheet_name}")

if __name__ == "__main__":
    service = authenticate_google_calendar()
    
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <tournament_id_1> <tournament_id_2> ...")
        sys.exit(1)

    tournament_ids = sys.argv[1:]
    all_tournament_data = []

    for tournament_id in tournament_ids:
        data = fetch_aes_data(tournament_id)
        if data:
            all_tournament_data.append(data)
            create_google_calendar_event(service, data)

    if all_tournament_data:
        write_to_google_sheets("AES Data", all_tournament_data)
