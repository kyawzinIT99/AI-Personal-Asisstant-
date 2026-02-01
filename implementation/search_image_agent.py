import os
import io
import re
import requests
import gspread
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def search_image(query, intent='search', chat_id=None):
    """
    Search for images in the Marketing Log Google Sheet.
    
    Args:
        query: Search keywords
        intent: 'search' (metadata only) or 'get' (download + send to Telegram)
        chat_id: Telegram chat ID (required for 'get' mode)
    
    Returns:
        Dictionary with image metadata and status
    """
    try:
        # Get sheet ID from environment
        sheet_id = os.getenv("MARKETING_LOG_SHEETS_ID") or os.getenv("GOOGLE_SHEETS_ID")
        if not sheet_id:
            return {
                "status": "error",
                "message": "MARKETING_LOG_SHEETS_ID not configured"
            }
        
        # Search in Google Sheets
        result = search_in_sheets(query, sheet_id)
        
        if result['result_status'] == 'not_found':
            return {
                "status": "success",
                "image_name": None,
                "image_id": None,
                "image_link": None,
                "result_status": "not_found",
                "message": "Image wasn't found in the database"
            }
        
        # If intent is 'get', download and send to Telegram
        telegram_status = "skipped"
        if intent == 'get' and chat_id and result.get('image_id'):
            telegram_status = download_and_send(result['image_id'], chat_id)
        
        return {
            "status": "success",
            "image_name": result['image_name'],
            "image_id": result['image_id'],
            "image_link": result['image_link'],
            "result_status": "found",
            "telegram_status": telegram_status
        }
        
    except Exception as e:
        print(f"Error in search_image: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }

def search_in_sheets(query, sheet_id):
    """
    Search for images in Google Sheets by keywords.
    
    Returns:
        Dictionary with image metadata or not_found status
    """
    TOKEN_FILE = 'token.json'
    
    if not os.path.exists(TOKEN_FILE):
        raise Exception("token.json missing - cannot search sheets")
    
    # Use OAuth2 token with Sheets scope
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/contacts.readonly',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1  # Default first sheet
    
    # Get all records
    records = worksheet.get_all_records()
    
    # Search in Title and Request columns (case-insensitive)
    query_lower = query.lower()
    
    for row in records:
        title = str(row.get('Title', '')).lower()
        request = str(row.get('Request', '')).lower()
        
        # Check if query matches title or request
        if query_lower in title or query_lower in request:
            # Extract Drive ID from Link
            link = row.get('Link', '')
            drive_id = extract_drive_id(link)
            
            print(f"Found image: {row.get('Title')} (ID: {drive_id})")
            
            return {
                'image_name': row.get('Title'),
                'image_id': drive_id,
                'image_link': link,
                'result_status': 'found'
            }
    
    print(f"No image found for query: {query}")
    return {'result_status': 'not_found'}

def extract_drive_id(drive_link):
    """
    Extract Google Drive file ID from various Drive URL formats.
    
    Examples:
        https://drive.google.com/file/d/FILE_ID/view
        https://drive.google.com/open?id=FILE_ID
    """
    if not drive_link:
        return None
    
    # Pattern 1: /d/FILE_ID/
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)
    
    # Pattern 2: ?id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)
    
    # Pattern 3: webViewLink format
    match = re.search(r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)
    
    return None

def download_and_send(file_id, chat_id):
    """
    Download image from Google Drive and send to Telegram.
    
    Returns:
        Status string: "sent", "error", or error message
    """
    try:
        # Download from Google Drive
        TOKEN_FILE = 'token.json'
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/contacts.readonly',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        service = build('drive', 'v3', credentials=creds)
        request = service.files().get_media(fileId=file_id)
        
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")
        
        print(f"Downloaded file from Drive (ID: {file_id})")
        
        # Send to Telegram
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return "No Telegram Bot Token configured"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        
        file_content.seek(0)  # Reset buffer position
        files = {'photo': ('image.png', file_content, 'image/png')}
        data = {'chat_id': chat_id}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print(f"Image sent to Telegram chat {chat_id}")
            return "sent"
        else:
            error_msg = f"Telegram API error: {response.status_code}"
            print(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Error downloading/sending: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg
