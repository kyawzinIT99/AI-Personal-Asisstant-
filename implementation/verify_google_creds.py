import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def main():
    creds = None
    
    # 1. Try to load existing token
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[ERROR] Failed to load token.json: {e}")

    # 2. If no valid token, let's log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] Credentials expired, attempting refresh...")
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"[ERROR] Refresh failed: {e}")
                creds = None

        if not creds:
            print("[INFO] No valid token found. Initiating OAuth flow (Local Server).")
            if not os.path.exists(CREDENTIALS_FILE):
                 print(f"[ERROR] {CREDENTIALS_FILE} not found.")
                 return
            
            try:
                # Use run_local_server for "http://localhost" redirect_uri
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                
                print("Launching browser for authentication...")
                # port=0 means pick an available port
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("[SUCCESS] Authentication successful. Token saved.")
            except Exception as e:
                print(f"[ERROR] OAuth flow failed: {e}")
                return

    # 3. Verify Gmail
    try:
        print("[INFO] Verifying Gmail service...")
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        print(f"[SUCCESS] Gmail verified. Found {len(labels)} labels.")
    except HttpError as error:
        print(f"[ERROR] An error occurred communicating with Gmail: {error}")
    except Exception as e:
        print(f"[ERROR] Unexpected error verifying Gmail: {e}")

    # 4. Verify Calendar
    try:
        print("[INFO] Verifying Calendar service...")
        service = build('calendar', 'v3', credentials=creds)
        page_token = None
        events_result = service.events().list(calendarId='primary', pageToken=page_token, maxResults=1).execute()
        print(f"[SUCCESS] Calendar verified. Access confirmed.")
    except HttpError as error:
        print(f"[ERROR] An error occurred communicating with Calendar: {error}")
    except Exception as e:
        print(f"[ERROR] Unexpected error verifying Calendar: {e}")

if __name__ == '__main__':
    main()
