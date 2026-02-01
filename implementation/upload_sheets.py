import json
import argparse
import sys
import os
import gspread
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Upload leads to Google Sheets.")
    parser.add_argument("--input", required=True, help="Input JSON file path (enriched leads)")
    args = parser.parse_args()
    
    sheet_id = os.getenv("APIFY_SHEETS_ID") or os.getenv("GOOGLE_SHEETS_ID")
    if not sheet_id:
        print("Error: APIFY_SHEETS_ID or GOOGLE_SHEETS_ID not found in .env")
        sys.exit(1)
        
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print(f"Error: {credentials_path} not found.")
        sys.exit(1)

    try:
        # Connect to Google Sheets
        gc = gspread.service_account(filename=credentials_path)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.sheet1  # Default to first sheet
        
        # Load leads
        with open(args.input, "r") as f:
            leads = json.load(f)
            
        if not leads:
            print("No leads to upload.")
            return

        # Check if sheet has existing headers
        existing_data = worksheet.get_all_values()
        
        if existing_data:
            # Use existing headers from the first row
            sheet_headers = existing_data[0]
            print(f"Found existing headers: {sheet_headers}")
            
            # Check for new columns in the data that aren't in the sheet
            # We want to ensure 'icebreaker' (and others) are captured
            data_keys = list(leads[0].keys())
            new_columns = [key for key in data_keys if key not in sheet_headers]
            
            if new_columns:
                print(f"Found new columns to add: {new_columns}")
                # Update headers in memory
                headers = sheet_headers + new_columns
                # Update headers in Sheet (row 1)
                # We need to rewrite the first row. 
                # gspread update using range
                worksheet.update("A1", [headers]) 
                print("Updated sheet headers with new columns.")
            else:
                headers = sheet_headers
        else:
            # Create new headers if sheet is empty
            all_keys = list(leads[0].keys())
            # Ensure icebreaker is last if possible, though strict ordering matters less now
            if "icebreaker" in all_keys:
                all_keys.remove("icebreaker")
                all_keys.sort()
                headers = all_keys + ["icebreaker"]
            else:
                all_keys.sort()
                headers = all_keys
            
            worksheet.append_row(headers)
            print("Added new headers to new sheet.")

        # Prepare rows matching the FINAL headers
        rows = []
        for lead in leads:
            row = []
            for col in headers:
                val = lead.get(col, "")
                if val is None:
                    val = ""
                row.append(str(val))
            rows.append(row)
            
        # Append data (skip header check as we handled it above)
        worksheet.append_rows(rows)
            
        # Append data

        print(f"Success: Uploaded {len(rows)} rows to Google Sheet.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during upload: {repr(e)}")
        # Detailed auth error help
        if "403" in str(e):
             print("\n[!] PERMISSION ERROR: Did you share the Google Sheet with the Service Account email?")
             print(f"    Email: {json.load(open(credentials_path))['client_email']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
