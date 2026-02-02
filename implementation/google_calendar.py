import os
import sys
import json
import argparse
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts.readonly'
]
TOKEN_FILE = 'token.json'

def extract_emails(input_data):
    """
    Extracts email addresses from a string or list of strings.
    Handles formats like:
    - "test@example.com"
    - "Name <test@example.com>"
    - "Name, test@example.com"
    """
    if not input_data:
        return []
        
    source_text = input_data
    if isinstance(input_data, list):
        source_text = ', '.join(input_data)
    
    # Simple but effective email regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, source_text)

def get_service():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("token.json not found. Please authenticate first.")
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        raise Exception(f"Failed to load credentials: {str(e)}")

def list_events(service, max_results=10, date_filter=None):
    try:
        if date_filter == 'tomorrow':
            target_date = datetime.now() + timedelta(days=1)
            time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            time_max = target_date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        elif date_filter == 'today':
            target_date = datetime.now()
            time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            time_max = target_date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        else:
            time_min = datetime.now().isoformat() + 'Z'
            time_max = None

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        output_events = []
        for event in events:
            # Skip birthday events as they are read-only
            if event.get('eventType') == 'birthday':
                continue
                
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            output_events.append({
                "id": event['id'],
                "summary": event.get('summary', '(No Title)'),
                "start": start,
                "end": end,
                "eventType": event.get('eventType', 'default')
            })
            
        return {"status": "success", "events": output_events, "date_filter": date_filter}
    except HttpError as error:
        return {"status": "error", "message": str(error)}

def create_event(service, summary, start_time_str, duration_minutes=60, description=None, attendees=None):
    try:
        # Parse start time. Assumes local time if no offset provided, or strict ISO.
        # For simplicity, we'll try to parse basic ISO: YYYY-MM-DDTHH:MM:SS
        try:
            start_dt = datetime.fromisoformat(start_time_str)
        except ValueError:
            return {"status": "error", "message": "Invalid start_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}
            
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC', # Ideally user's timezone, but defaulting to UTC/local for simplicity
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }

        if attendees:
            emails = extract_emails(attendees)
            if emails:
                event['attendees'] = [{'email': email} for email in emails]

        event = service.events().insert(calendarId='primary', body=event).execute()
        return {
            "status": "success", 
            "event_id": event.get('id'), 
            "link": event.get('htmlLink')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_event(service, event_id):
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        return {
            "status": "success",
            "id": event.get('id'),
            "summary": event.get('summary'),
            "description": event.get('description'),
            "start": event['start'].get('dateTime', event['start'].get('date')),
            "end": event['end'].get('dateTime', event['end'].get('date')),
            "attendees": [a.get('email') for a in event.get('attendees', [])]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def update_event(service, event_id, summary=None, start_time_str=None, duration_minutes=None, description=None, attendees=None):
    try:
        # First retrieve the event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        if summary:
            event['summary'] = summary
        
        if description:
            event['description'] = description

        if start_time_str:
            try:
                start_dt = datetime.fromisoformat(start_time_str)
                
                # Calculate duration from EXISTING event details before we overwrite them
                # Use replace('Z',...) to handle UTC 'Z' notation if present
                current_start_str = event['start'].get('dateTime', '')
                current_end_str = event['end'].get('dateTime', '')
                
                duration = timedelta(minutes=60) # Default
                
                if current_start_str and current_end_str:
                    old_start = datetime.fromisoformat(current_start_str.replace('Z', '+00:00'))
                    old_end = datetime.fromisoformat(current_end_str.replace('Z', '+00:00'))
                    duration = old_end - old_start

                # Now apply new start time
                event['start']['dateTime'] = start_dt.isoformat()
                
                # Calculate new end time
                if duration_minutes:
                    end_dt = start_dt + timedelta(minutes=duration_minutes)
                else:
                    # Maintain existing duration
                    end_dt = start_dt + duration
                
                event['end']['dateTime'] = end_dt.isoformat()
            except ValueError:
                return {"status": "error", "message": "Invalid start_time format"}
        elif duration_minutes:
            # Only duration changed, start time same
            start_dt = datetime.fromisoformat(event['start'].get('dateTime').replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            event['end']['dateTime'] = end_dt.isoformat()

        if attendees is not None:
             emails = extract_emails(attendees)
             # Note: if emails is empty but attendees was not None (e.g. empty string), we might want to clear attendees?
             # But usually update requests expect the explicit list.
             # If passed implicit empty string, maybe clear?
             # For now, if we found emails, update. If we didn't, but input was valid string but no emails, 
             # maybe user wanted to clear?
             # Let's stick to: if emails found, set them. If user passed empty string, emails is [], so event['attendees'] = []
             event['attendees'] = [{'email': email} for email in emails]

        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return {"status": "success", "event_id": updated_event.get('id'), "link": updated_event.get('htmlLink')}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_event(service, event_id):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"status": "success", "message": "Event deleted"}
    except HttpError as error:
        # Handle specific API errors
        error_content = error.content.decode('utf-8')
        if 'birthday' in error_content or 'eventTypeRestriction' in error_content:
             return {"status": "error", "message": "Cannot delete this event (it might be a read-only birthday)."}
        return {"status": "error", "message": str(error)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Google Calendar Tool')
    parser.add_argument('--action', required=True, choices=['list', 'create'])
    parser.add_argument('--max_results', type=int, default=10, help='Max results for list')
    parser.add_argument('--date', help='Date filter for list (today, tomorrow)')
    parser.add_argument('--summary', help='Event summary')
    parser.add_argument('--start_time', help='Event start time (ISO)')
    parser.add_argument('--duration_minutes', type=int, default=60, help='Event duration in minutes')
    parser.add_argument('--description', help='Event description')
    
    args = parser.parse_args()
    service = get_service()
    
    if args.action == 'list':
        print(json.dumps(list_events(service, args.max_results, args.date)))
        
    elif args.action == 'create':
        if not args.summary or not args.start_time:
            print(json.dumps({"status": "error", "message": "Missing summary or start_time for create"}))
            sys.exit(1)
        print(json.dumps(create_event(service, args.summary, args.start_time, args.duration_minutes, args.description)))

if __name__ == '__main__':
    main()
