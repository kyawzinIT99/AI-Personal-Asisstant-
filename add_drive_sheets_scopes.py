#!/usr/bin/env python3
"""
Re-authenticate Google OAuth to add Drive and Sheets scopes.
This will update your token.json with the additional permissions needed.
"""

import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# All scopes needed for the application
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.file',  # For Drive upload
    'https://www.googleapis.com/auth/spreadsheets'  # For Sheets logging
]

def main():
    creds = None
    
    # Check if token.json exists
    if os.path.exists('token.json'):
        print("Found existing token.json")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If credentials are invalid or don't have all scopes, re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Attempting to refresh token...")
            try:
                creds.refresh(Request())
                print("✓ Token refreshed successfully")
            except Exception as e:
                print(f"✗ Refresh failed: {e}")
                print("Need to re-authenticate...")
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                print("ERROR: credentials.json not found!")
                print("Please download OAuth 2.0 credentials from Google Cloud Console")
                sys.exit(1)
            
            print("\nStarting OAuth flow...")
            print("This will open a browser window for authentication.")
            print(f"Requesting scopes:")
            for scope in SCOPES:
                print(f"  - {scope}")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✓ Authentication successful!")
    
    # Save the credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("\n✓ token.json updated with all required scopes:")
    print("  - Gmail")
    print("  - Calendar")
    print("  - Drive (file upload)")
    print("  - Sheets (logging)")
    print("\nYou can now use the Image Agent with Drive upload!")

if __name__ == '__main__':
    main()
