import requests
import json
import csv
import gspread
import sys
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
        print(f"Data fetched for tournament {tournament_id}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for tournament {tournament_id}: {e}")
        return None

def format_date(date_str):
    """Convert ISO date to 'Month Day, Year' with correct suffix."""
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", ""))
            day = dt.day
            suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            return dt.strftime(f"%B {day}{suffix}, %Y")
        except ValueError:
            return date_str
    return ""

def write_to_google_sheets(sheet_name, tournament_list):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    
    sheet = client.open(sheet_name).sheet1
    sheet.clear()

    # Define headers
    headers = [
        "eventId", 
        "name", 
        "locationName", 
        "hostName", 
        "startDate", 
        "endDate",
        "registrationOpenDate", 
        "registrationCloseDate", 
        "lateRegistrationDate", 
        "isUSAV", 
        "gender", 
        "ballerTvEnabled"
    ]
    sheet.append_row(headers)

    # Write tournament data with actual formulas for hyperlinks
    for data in tournament_list:
        aes_url = f"https://www.advancedeventsystems.com/events/{data.get('eventId')}"
        google_maps_url = f"https://www.google.com/maps/search/{data.get('locationName').replace(' ', '+')}" if data.get("locationName") else ""

        name_hyperlink = f'=HYPERLINK("{data.get("website")}", "{data.get("name")}")' if data.get("website") else data.get("name")
        event_id_hyperlink = f'=HYPERLINK("{aes_url}", "{data.get("eventId")}")'
        location_hyperlink = f'=HYPERLINK("{google_maps_url}", "{data.get("locationName")}")' if data.get("locationName") else ""

        row = [
            event_id_hyperlink,
            name_hyperlink,
            location_hyperlink,
            data.get("hostName"),
            format_date(data.get("startDate")),
            format_date(data.get("endDate")),
            format_date(data.get("registrationOpenDate")),
            format_date(data.get("registrationCloseDate")),
            format_date(data.get("lateRegistrationDate")),
            data.get("affiliation", {}).get("isUSAV"),
            ", ".join(g.get("displayName") for g in data.get("genderClassTypes", [])),
            data.get("ballerTvEnabled")
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")

    print(f"Data successfully written to Google Sheets: {sheet_name}")

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
