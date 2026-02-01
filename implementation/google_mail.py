import os
import sys
import json
import base64
import argparse
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = 'token.json'

def get_service():
    if not os.path.exists(TOKEN_FILE):
        print(json.dumps({"status": "error", "message": "token.json not found. Please authenticate first."}))
        sys.exit(1)
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Failed to load credentials: {str(e)}"}))
        sys.exit(1)

def send_email(service, to, subject, body):
    try:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        message = service.users().messages().send(userId='me', body=body).execute()
        return {"status": "success", "message_id": message['id']}
    except HttpError as error:
        return {"status": "error", "message": str(error)}

def list_emails(service, max_results=10, query=None):
    try:
        kwargs = {'userId': 'me', 'maxResults': max_results}
        if query:
            kwargs['q'] = query
            
        results = service.users().messages().list(**kwargs).execute()
        messages = results.get('messages', [])
        
        output_messages = []
        if messages:
            for msg in messages:
                # Batch these or do a get for snippets? 
                # For simplicity/speed, we'll fetch details for each to get subject/sender
                # Real implementation might want batchRequest for performance if max_results is high
                try:
                    msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                    headers = msg_detail.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(no subject)')
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(unknown)')
                    output_messages.append({
                        "id": msg['id'],
                        "snippet": msg_detail.get('snippet', ''),
                        "subject": subject,
                        "from": sender
                    })
                except:
                    continue
                    
        return {"status": "success", "messages": output_messages}
    except HttpError as error:
        return {"status": "error", "message": str(error)}

def read_email(service, message_id):
    try:
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        headers = message.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(no subject)')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(unknown)')
        
        # Simple body extraction (prefer text/plain)
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode()
                        break
        else:
             data = message['payload']['body'].get('data')
             if data:
                 body = base64.urlsafe_b64decode(data).decode()
                 
        return {
            "status": "success",
            "id": message['id'],
            "subject": subject,
            "from": sender,
            "body": body,
            "threadId": message.get('threadId')
        }
    except HttpError as error:
        return {"status": "error", "message": str(error)}

def create_draft(service, to, subject, body):
    if not to or not subject or not body:
        return {"status": "error", "message": "Missing required fields: to, subject, or body"}
    try:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'message': {'raw': raw}}
        
        draft = service.users().drafts().create(userId='me', body=body).execute()
        return {"status": "success", "draft_id": draft['id'], "message": "Draft created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def reply_email(service, message_id, body):
    if not message_id or not body:
        return {"status": "error", "message": "Missing required fields: message_id or body"}
    try:
        # Get original message to find threadId and subject
        original_msg = service.users().messages().get(userId='me', id=message_id, format='metadata').execute()
        thread_id = original_msg.get('threadId')
        headers = original_msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        
        # Determine headers for reply
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
            
        # We need to find the 'To' address (which is the 'From' of the original email, or Reply-To)
        # For simplicity, we'll take the 'From' of the original
        recipient = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')

        message = MIMEText(body)
        message['to'] = recipient
        message['subject'] = subject
        
        # Add references if available (for proper threading clients often look at In-Reply-To and References)
        # But Gmail API 'threadId' does the heavy lifting for grouping in Gmail.
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw, 'threadId': thread_id}
        
        sent_message = service.users().messages().send(userId='me', body=body).execute()
        return {"status": "success", "message_id": sent_message['id'], "thread_id": sent_message['threadId']}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_email(service, message_id):
    if not message_id:
        return {"status": "error", "message": "Missing message_id"}
    try:
        # We use trash instead of delete for safety
        service.users().messages().trash(userId='me', id=message_id).execute()
        return {"status": "success", "message": "Message moved to trash"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Google Mail Tool')
    parser.add_argument('--action', required=True, choices=['send', 'list', 'read'])
    parser.add_argument('--to', help='Recipient email')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body')
    parser.add_argument('--max_results', type=int, default=10, help='Max results for list')
    parser.add_argument('--query', help='Query string for list')
    parser.add_argument('--message_id', help='Message ID for read')
    
    args = parser.parse_args()
    service = get_service()
    
    if args.action == 'send':
        if not args.to or not args.subject or not args.body:
            print(json.dumps({"status": "error", "message": "Missing arguments for send"}))
            sys.exit(1)
        print(json.dumps(send_email(service, args.to, args.subject, args.body)))
        
    elif args.action == 'list':
        print(json.dumps(list_emails(service, args.max_results, args.query)))
        
    elif args.action == 'read':
        if not args.message_id:
            print(json.dumps({"status": "error", "message": "Missing message_id for read"}))
            sys.exit(1)
        print(json.dumps(read_email(service, args.message_id)))

if __name__ == '__main__':
    main()
