import os
import json
import requests
import time
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

# Initialize clients
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

json2video_api_key = os.getenv("JSON2VIDEO_API_KEY")
SHEET_ID = os.getenv("JSON2VIDEO_SHEET_ID")

def get_gspread_client():
    if os.path.exists('service_account.json'):
        return gspread.service_account(filename='service_account.json')
    return None

def get_column_idx(headers, possible_names):
    """Returns 1-based index of first matching header, or None."""
    for i, h in enumerate(headers):
        if h.lower().strip() in [p.lower() for p in possible_names]:
            return i + 1
    return None

def generate_video_workflow(subject=None):
    """
    Orchestrates the Faceless Video workflow.
    Reads/Writes to Google Sheet.
    """
    if not openai_client or not json2video_api_key:
        return {"status": "error", "message": "Missing API keys"}

    current_subject = subject
    row_number = None
    worksheet = None
    
    # Column Indices (to be found dynamically)
    col_subject = None
    col_status = None
    col_url = None
    col_project_id = None

    # 1. Connect to Sheet
    if SHEET_ID:
        try:
            gc = get_gspread_client()
            if gc:
                sh = gc.open_by_key(SHEET_ID)
                worksheet = sh.get_worksheet(0)
                headers = worksheet.row_values(1)
                
                col_subject = get_column_idx(headers, ['Subject', 'Topic', 'Title'])
                col_status = get_column_idx(headers, ['Status', 'Creation Status', 'State'])
                col_url = get_column_idx(headers, ['Video URL', 'URL', 'Link', 'Result'])
                col_project_id = get_column_idx(headers, ['Project ID', 'Job ID', 'ID'])
                
                # If reading from sheet (no subject provided)
                if not current_subject and col_subject:
                    records = worksheet.get_all_records()
                    for i, record in enumerate(records):
                        # Gspread records dict keys match headers exactly
                        rec_subject = None
                        rec_url = None
                        
                        # Find values using header names corresponding to found indices
                        # (A bit tricky since get_all_records uses keys, but we have indices. 
                        #  Better to just use indices and iterate rows if get_all_records is ambiguous, 
                        #  but records is cleaner. Let's use header string lookup.)
                        
                        header_subject = headers[col_subject-1]
                        header_url = headers[col_url-1] if col_url else None
                        
                        val_subject = record.get(header_subject)
                        val_url = record.get(header_url) if header_url else None
                        
                        if val_subject and not val_url:
                            current_subject = val_subject
                            row_number = i + 2
                            print(f"Found subject in row {row_number}: {current_subject}")
                            break
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Sheet Error: {repr(e)}")
            if not subject:
                return {"status": "error", "message": f"Sheet Error: {repr(e)}"}

    if not current_subject:
        return {"status": "error", "message": "No subject provided and none found in Sheet."}

    # 2. Update Sheet Status to 'Processing'
    if worksheet and row_number and col_status:
        try:
            worksheet.update_cell(row_number, col_status, "Processing")
        except: pass

    try:
        # 3. Generate Scripts & Rankings
        scripts = generate_scripts(current_subject)
        rankings = generate_rankings(current_subject)
        
        # 4. JSON2Video Payload
        movie_payload = {
            "template": "9XtfsD0C3Tb2vbvfc84d",
            "variables": {
                "title": current_subject,
                "voiceModel": "elevenlabs",
                "voice.ConnectionID": "my-elevenlabs-connection", 
                "voiceID": "aD6riP1btT197c6dACmy",
                "imageModel": "flux-pro",
                "introImagePrompt": scripts.get('introImagePrompt', ''),
                "introVoiceoverText": scripts.get('introVoiceoverText', ''),
                "outroImagePrompt": scripts.get('outroImagePrompt', ''),
                "outroVoiceoverText": scripts.get('outroVoiceoverText', ''),
                "ranking": rankings
            }
        }
        
        # 5. Call API
        j2v_url = "https://api.json2video.com/v2/movies"
        headers = {
            "Authorization": f"Bearer {json2video_api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(j2v_url, json=movie_payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            project_id = data.get('project')
            
            # Save Project ID to Sheet if possible
            if worksheet and row_number and col_project_id:
                try: 
                    worksheet.update_cell(row_number, col_project_id, project_id)
                except: pass
            
            return {
                "status": "success", 
                "message": "Video generation started", 
                "project_id": project_id,
                "subject": current_subject
            }
        else:
            return {"status": "error", "message": f"json2video error: {response.text}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_video_for_subject(subject):
    return generate_video_workflow(subject=subject)

def generate_scripts(subject):
    system_prompt = """
    You are a creative assistant for simple Top 10 videos.
    Output JSON with: introVoiceoverText, introImagePrompt, outroVoiceoverText, outroImagePrompt.
    """
    user_prompt = f"Subject: {subject}. Generate intro/outro."
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def generate_rankings(subject):
    system_prompt = """
    Generate a Top 10 list for the subject. Count down from 10 to 1.
    Output JSON array of objects with keys: voiceoverText, imagePrompt, lowerThirdText.
    """
    user_prompt = f"Subject: {subject}. Generate top 10 rankings."
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        response_format={"type": "json_object"}
    )
    content = json.loads(response.choices[0].message.content)
    if 'rankings' in content: return content['rankings']
    if 'items' in content: return content['items']
    return []

def check_video_status(project_id):
    if not json2video_api_key:
         return {"status": "error", "message": "Missing API keys"}
         
    url = f"https://api.json2video.com/v2/movies?project={project_id}"
    headers = {"Authorization": f"Bearer {json2video_api_key}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            movie = data.get('movie', {})
            status = movie.get('status')
            video_url = movie.get('url')
            
            # --- UPDATE SHEET IF DONE ---
            if status == 'done' and video_url and SHEET_ID:
                try:
                    gc = get_gspread_client()
                    if gc:
                        sh = gc.open_by_key(SHEET_ID)
                        worksheet = sh.get_worksheet(0)
                        
                        # Find row by Project ID (assuming we saved it)
                        # This is expensive (searching all rows). 
                        # Optimization: We check if we can find the project_id in the cell records.
                        
                        headers = worksheet.row_values(1)
                        col_project_id = get_column_idx(headers, ['Project ID', 'Job ID', 'ID'])
                        col_url = get_column_idx(headers, ['Video URL', 'URL', 'Link', 'Result'])
                        col_status = get_column_idx(headers, ['Status', 'Creation Status'])

                        if col_project_id:
                            # Search for project_id 
                            cell = worksheet.find(project_id)
                            if cell:
                                row_num = cell.row
                                if col_url: worksheet.update_cell(row_num, col_url, video_url)
                                if col_status: worksheet.update_cell(row_num, col_status, "Done")
                except Exception as e:
                    print(f"Sheet update error: {e}")
            # ---------------------------

            return {"status": "success", "job_status": status, "video_url": video_url}
        else:
             return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
