import os
import json
import requests
import io
from openai import OpenAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

def generate_image_workflow(image_title, image_prompt, chat_id=None):
    """
    Orchestrates the image generation workflow:
    1. Refine prompt using OpenAI
    2. Generate image using DALL-E 3
    3. Upload to Google Drive
    4. Log to Google Sheets
    5. Send to Telegram (optional)
    """
    try:
        # 1. Refine Prompt
        print(f"Refining prompt for: {image_prompt}")
        refined_prompt = refine_prompt(image_prompt)
        
        # 2. Generate Image
        print(f"Generating image with prompt: {refined_prompt}")
        image_url = generate_image(refined_prompt)
        
        if not image_url or "placeholder" in image_url:
            # If mock, we persist mock
            pass
        elif not image_url.startswith("http"):
             raise Exception("Failed to generate image")

        # 3. Upload to Drive
        print("Uploading to Google Drive...")
        drive_link = upload_to_drive(image_url, image_title)
        
        # 4. Log to Sheets
        print("Logging to Google Sheets...")
        log_to_sheets(image_title, image_prompt, drive_link, image_url)
        
        # 5. Send to Telegram
        telegram_status = "Skipped"
        if chat_id:
             telegram_status = send_to_telegram(chat_id, image_url)
             
        return {
            "status": "success",
            "image_title": image_title,
            "refined_prompt": refined_prompt,
            "image_url": image_url,
            "drive_link": drive_link,
            "telegram_status": telegram_status
        }
        
    except Exception as e:
        print(f"Error in image workflow: {e}")
        return {"status": "error", "message": str(e)}

def refine_prompt(original_prompt):
    if not openai_client:
        return original_prompt + " (Mock Refined)"
        
    system_message = """
    You are an expert image prompt engineer. 
    Expand the user's input into a detailed DALL-E 3 prompt.
    Include subject, background, style, mood, lighting, and details.
    Output ONLY the prompt, no other text.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": original_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Refine prompt error: {e}")
        return original_prompt

def generate_image(prompt):
    if not openai_client:
        return "https://via.placeholder.com/1024?text=Mock+Image"
        
    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt[:4000], # Limit prompt length
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"Image gen error: {e}")
        return "https://via.placeholder.com/1024?text=Error+Generating+Image"

def upload_to_drive(image_url, title):
    # Folder ID from user request
    FOLDER_ID = "1d71dtq308dJ7RfppeBycqSapKTpbpGOl"
    TOKEN_FILE = 'token.json'
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    try:
        # Download image content
        if "placeholder" in image_url:
            return "https://drive.google.com/mock-link"

        response = requests.get(image_url)
        if response.status_code != 200:
            return f"Failed to download image: HTTP {response.status_code}"
        
        image_content = io.BytesIO(response.content)
        
        # Auth using OAuth2 token (same as Gmail/Calendar)
        if not os.path.exists(TOKEN_FILE):
            return "token.json missing - please authenticate first"

        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': f"{title}.png",
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(image_content, mimetype='image/png', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"Drive upload successful: {file.get('webViewLink')}")
        return file.get('webViewLink')
    except Exception as e:
        print(f"Drive upload error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error uploading to Drive: {e}"

def log_to_sheets(title, request_prompt, drive_link, image_url):
    sheet_id = os.getenv("MARKETING_LOG_SHEETS_ID") or os.getenv("GOOGLE_SHEETS_ID")
    TOKEN_FILE = 'token.json'
    
    if not sheet_id:
        print("MARKETING_LOG_SHEETS_ID or GOOGLE_SHEETS_ID missing")
        return
        
    try:
        if not os.path.exists(TOKEN_FILE):
            print("token.json missing - cannot log to sheets")
            return

        # Use OAuth2 token with Sheets scope
        from google.oauth2.credentials import Credentials
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.sheet1 # Default first sheet
        
        # Columns: Title, Type, Request, ID, Link, Post
        row = [
            title,
            "Image",
            request_prompt,
            "", # ID placeholder
            drive_link,
            "" # Post placeholder
        ]
        
        worksheet.append_row(row)
        print(f"Logged to sheets: {title}")
    except Exception as e:
        print(f"Sheets logging error: {e}")
        import traceback
        traceback.print_exc()

def send_to_telegram(chat_id, image_url):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return "No Bot Token"
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        requests.post(url, json={"chat_id": chat_id, "photo": image_url})
        return "Sent"
    except Exception as e:
        return f"Error sending to Telegram: {e}"
