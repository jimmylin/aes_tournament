Sure! Here's the markdown for your README:  

```markdown
# AES Tournament Scraper

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)  
A Python script to fetch volleyball tournament data from [Advanced Event Systems (AES)](https://www.advancedeventsystems.com) and export it to **Google Sheets** with hyperlinks for quick navigation.

## 🚀 Features

- Fetches tournament data using the AES API.  
- Formats dates into a human-readable format (e.g., **January 1st, 2025**).  
- Generates **hyperlinks**:
  - **Tournament ID** → Links to AES event page  
  - **Tournament Name** → Links to event’s website (if available)  
  - **Location** → Links to Google Maps  
- Saves the data directly to a Google Sheet.  

## 📦 Installation

### 1. Clone the Repository
```sh
git clone https://github.com/jimmylin/aes_tournament.git
cd aes_tournament
```

### 2. Install Dependencies  
Make sure you have Python **3.8+** installed, then run:
```sh
pip install -r requirements.txt
```

### 3. Set Up Google Sheets API  
To enable writing data to Google Sheets:  
1. Go to [Google Cloud Console](https://console.cloud.google.com/)  
2. Create a new project & enable the **Google Sheets API**  
3. Create a **service account** and download the `credentials.json` file  
4. Place `credentials.json` in the project root  

## 🔧 Usage

### Run the script with tournament IDs:  
```sh
python scrape.py <tournament_id_1> <tournament_id_2> ...
```
Example:  
```sh
python scrape.py 37945 37337
```

### Expected Output:
The script fetches tournament details and writes them to a **Google Sheet** named `"AES Data"`.

### Google Sheets Output:
| eventId | name | locationName | hostName | startDate | endDate | registrationOpenDate | registrationCloseDate | lateRegistrationDate | isUSAV | gender | ballerTvEnabled |
|---------|------|-------------|----------|-----------|---------|----------------------|----------------------|-------------------|-------|--------|----------------|
| [🔗](https://www.advancedeventsystems.com/events/37945) 37945 | [🏐 FALL NETFEST BOYS](http://www.dcpgsports.com/vb-tournaments-24-25.html) | 📍 [Washington, DC](https://www.google.com/maps/search/Washington,+DC) | DC PG Sports | October 12th, 2024 | October 13th, 2024 | August 1st, 2024 | September 20th, 2024 | October 5th, 2024 | True | Boys | Yes |

## 📝 Notes

- **Google Sheets name**: The script writes to `"AES Data"`. If needed, update the script with your preferred sheet name.  
- **Hyperlinks**: Ensure that Google Sheets is set to accept formulas (`value_input_option="USER_ENTERED"`).  
- **Error Handling**: If the AES API fails, it prints an error message instead of crashing.  

## 🛠️ Future Improvements

- Add caching to reduce redundant API requests.  
- Implement a web UI for easier input of tournament IDs.  

## 📄 License
This project is licensed under the MIT License.  
```

Just copy and paste this into your `README.md` file. Let me know if you need any tweaks! 🚀
