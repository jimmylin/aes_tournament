import requests
import json
import gspread
import sys
import urllib.parse
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

def fetch_aes_data(tournament_id):
    url = f"https://www.advancedeventsystems.com/api/landing/events/{tournament_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
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

def load_existing_data(sheet):
    """Load existing tournament data from Google Sheets."""
    data = sheet.get_all_values()
    if not data:
        return {}, []

    headers = data[0]
    rows = data[1:]

    existing_tournaments = {}
    for row in rows:
        event_id = row[0].split('"')[3] if "HYPERLINK" in row[0] else row[0]  # Extract eventId from hyperlink
        existing_tournaments[event_id] = row

    return existing_tournaments, headers

def write_to_google_sheets(sheet_name, tournament_list):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    
    sheet = client.open(sheet_name).sheet1

    # Load existing tournaments before updating
    existing_tournaments, headers = load_existing_data(sheet)

    # Define human-readable headers
    readable_headers = [
        "AES Link", "Tournament Name", "Location", 
        "Start Date", "End Date", 
        "Reg Opens", "Reg Closes", "Late Reg", "USAV Sanctioned"
    ]

    # Write headers if missing
    if not headers or headers != readable_headers:
        sheet.clear()
        sheet.append_row(readable_headers)

    updated_rows = []
    for data in tournament_list:
        event_id = str(data.get("eventId"))
        aes_url = f"https://www.advancedeventsystems.com/events/{event_id}"
        event_id_hyperlink = f'=HYPERLINK("{aes_url}", "{event_id}")'

        name_hyperlink = f'=HYPERLINK("{data.get("website")}", "{data.get("name")}")' if data.get("website") else data.get("name")

        # Google Maps Hyperlink
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

        # Update existing tournament or add a new one
        if event_id in existing_tournaments:
            existing_tournaments[event_id] = row
        else:
            updated_rows.append(row)

    # Update sheet with new data (preserving manual entries)
    sheet.clear()
    sheet.append_row(readable_headers)  # Always ensure headers are written
    for row in existing_tournaments.values():
        sheet.append_row(row, value_input_option="USER_ENTERED")
    for row in updated_rows:
        sheet.append_row(row, value_input_option="USER_ENTERED")

    print(f"✅ Data successfully written to Google Sheets: {sheet_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <tournament_id_1> <tournament_id_2> ...")
        sys.exit(1)
    
    tournament_ids = sys.argv[1:]
    all_tournament_data = []

    for tournament_id in tournament_ids:
        data = fetch_aes_data(tournament_id)
        if data:
            all_tournament_data.append(data)

    if all_tournament_data:
        write_to_google_sheets("AES Data", all_tournament_data)
