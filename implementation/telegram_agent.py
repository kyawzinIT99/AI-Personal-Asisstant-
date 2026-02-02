import os
import time
import requests
import json
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add implementation folder to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import google_calendar
import google_mail
import google_contacts
import weather_agent
import web_agent
import image_agent
import chat_agent
import search_image_agent
import blog_agent
import faceless_video_agent
import stripe_utils
import scrape_apify

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_updates(offset=None):
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return None

def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def parse_intent(text):
    """
    Use OpenAI to categorize the user's intent and extract parameters.
    """
    client = chat_agent.get_openai_client()
    if not client:
        return {"intent": "chat", "params": {"query": text}}

    # Inject current time so the LLM can resolve relative dates (today, tomorrow, etc.)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")

    system_prompt = f"""
    You are an intent classifier for a personal assistant. 
    Current Time: {now_str}
    
    Categorize the user request into one of these intents and extract parameters in JSON format.
    
    Intents:
    - calendar_list: {{"date": "today"|"tomorrow"|null}}
    - calendar_create: {{"summary": "set", "start_time": "ISO format", "duration": 60}}
    - calendar_update: {{"target_event": "name of event to move", "new_start_time": "ISO format", "date": "today"|"tomorrow"}}
    - calendar_delete: {{"target_event": "name of event to delete", "date": "today"|"tomorrow"}}
    - mail_list: {{"query": "string"|null, "max_results": 5}}
    - mail_send: {{"to": "email@example.com", "subject": "string", "body": "string"}}
    - mail_reply: {{"message_id": "string"|null, "body": "reply text"}}
    - mail_draft: {{"to": "email@example.com", "subject": "string", "body": "string"}}
    - contact_search: {{"query": "name or email"}}
    - lead_gen: {{"query": "job title", "location": "city or country", "limit": 5}}
    - weather: {{"city": "name"}}
    - web_search: {{"query": "search term"}}
    - image_gen: {{"prompt": "dalle prompt", "title": "short title"}}
    - image_search: {{"query": "search term for image"}}
    - blog_gen: {{"topic": "blog topic", "audience": "target audience"}}
    - video_gen: {{"subject": "video subject"}}
    - video_status: {{"project_id": "optional id"}}
    - subscription_status: {{"email": "email address"}}
    - chat: {{"query": "original text"}} (fallback for general questions)

    Rules for calendar_list:
    - Recognize queries about schedule, calendar, events, appointments
    - Examples:
      * "What's on my calendar today?" → {{"intent": "calendar_list", "params": {{"date": "today"}}}}
      * "Show tomorrow's schedule" → {{"intent": "calendar_list", "params": {{"date": "tomorrow"}}}}
      * "What's my schedule for tomorrow?" → {{"intent": "calendar_list", "params": {{"date": "tomorrow"}}}}
      * "Show my calendar" → {{"intent": "calendar_list", "params": {{"date": null}}}}

    Rules for calendar_update:
    - Recognize "reschedule", "move", "change time", "delay"
    - Extract the event name to target_event
    - extract the new start time to new_start_time
    - Examples:
      * "Reschedule dinner to 9pm" → {{"intent": "calendar_update", "params": {{"target_event": "dinner", "new_start_time": "202x-MM-DDT21:00:00", "date": "today"}}}}
      * "Move tomorrow's meeting to 10am" → {{"intent": "calendar_update", "params": {{"target_event": "meeting", "new_start_time": "202x-MM-DDT10:00:00", "date": "tomorrow"}}}}

    Rules for calendar_delete:
    - Recognize "delete", "remove", "cancel", "clear"
    - PRIORITY: If user says "delete" or "cancel", it is ALWAYS calendar_delete, never update.
    - Examples:
      * "Delete dinner" → {{"intent": "calendar_delete", "params": {{"target_event": "dinner", "date": "today"}}}}
      * "Cancel the meeting tomorrow" → {{"intent": "calendar_delete", "params": {{"target_event": "meeting", "date": "tomorrow"}}}}
      * "Remove the event at 9pm" → {{"intent": "calendar_delete", "params": {{"target_event": "event", "date": "today"}}}}

    Rules for mail_send:
    - ALWAYS extract the recipient email address into the "to" field
    - Look for patterns like: name@domain.com, user@gmail.com, etc.
    - Examples:
      * "send email to john@example.com" → {{"intent": "mail_send", "params": {{"to": "john@example.com", "subject": "", "body": ""}}}}
      * "email test@gmail.com with subject Hello" → {{"intent": "mail_send", "params": {{"to": "test@gmail.com", "subject": "Hello", "body": ""}}}}
      * "send message to user@company.com saying Thanks" → {{"intent": "mail_send", "params": {{"to": "user@company.com", "subject": "", "body": "Thanks"}}}}
    - If NO email address is found in the text, use intent="chat" and ask for clarification
    
    Rules for mail_reply:
    - Extract the reply body text
    - If user mentions "latest email" or "last email", set message_id to null (we'll fetch latest)
    - Examples:
      * "reply to latest email: Noted" → {{"intent": "mail_reply", "params": {{"message_id": null, "body": "Noted"}}}}
      * "reply Noted" → {{"intent": "mail_reply", "params": {{"message_id": null, "body": "Noted"}}}}
      * "respond to last email saying Thanks" → {{"intent": "mail_reply", "params": {{"message_id": null, "body": "Thanks"}}}}
    
    Rules for mail_draft:
    - Extract recipient, subject, and body like mail_send
    - Examples:
      * "draft email to john@example.com with subject Meeting" → {{"intent": "mail_draft", "params": {{"to": "john@example.com", "subject": "Meeting", "body": ""}}}}
      * "create draft to test@gmail.com about Project Update" → {{"intent": "mail_draft", "params": {{"to": "test@gmail.com", "subject": "Project Update", "body": ""}}}}
    
    Rules for lead_gen:
    - Recognize "find leads", "scrape leads", "get emails", "find people"
    - Extract job title (query) and location
    - Default limit is 5, max is 10
    - Examples:
      * "Find leads for CEO in New York" → {{"intent": "lead_gen", "params": {{"query": "CEO", "location": "New York", "limit": 5}}}}
      * "Scrape 10 leads for Software Engineer in London" → {{"intent": "lead_gen", "params": {{"query": "Software Engineer", "location": "London", "limit": 10}}}}

    Rules for image_search:
    - Extract search query for finding images in Google Drive
    - Examples:
      * "find image of legendary watch" → {{"intent": "image_search", "params": {{"query": "legendary watch"}}}}
      * "search for sunset image" → {{"intent": "image_search", "params": {{"query": "sunset"}}}}
      * "A legendary watch is being found now" → {{"intent": "image_search", "params": {{"query": "legendary watch"}}}}

    Rules for blog_gen:
    - Extract topic and intended audience
    - Examples:
      * "write a blog about AI for beginners" → {{"intent": "blog_gen", "params": {{"topic": "AI", "audience": "beginners"}}}}
      * "create a post about healthy eating" → {{"intent": "blog_gen", "params": {{"topic": "healthy eating", "audience": "general"}}}}

    Rules for video_gen:
    - Extract the subject of the video
    - Examples:
      * "make a video about space travel" → {{"intent": "video_gen", "params": {{"subject": "space travel"}}}}
      * "generate a video on how to cook pasta" → {{"intent": "video_gen", "params": {{"subject": "how to cook pasta"}}}}

    Rules for video_status:
    - Check if user is asking about video progress
    - Examples:
      * "is my video done?" → {{"intent": "video_status", "params": {{}}}}
      * "check status of video 123" → {{"intent": "video_status", "params": {{"project_id": "123"}}}}
    
    Rules for subscription_status:
    - Check if user has active premium plan
    - Extract email if provided, otherwise might need to ask or use default (if we had user mapping)
    - Examples:
      * "am I subscribed?" → {{"intent": "subscription_status", "params": {{}}}}
      * "check subscription for test@example.com" → {{"intent": "subscription_status", "params": {{"email": "test@example.com"}}}}

    Other rules:
    - Return ONLY valid JSON
    - If the user asks for "tomorrow's schedule", intent is calendar_list with date="tomorrow"
    - If the user asks for "weather in London", intent is weather with city="London"
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={ "type": "json_object" }
        )
        parsed = json.loads(completion.choices[0].message.content)
        
        # Fallback: If intent is mail_send but no 'to' field, try regex extraction
        if parsed.get("intent") == "mail_send":
            to_addr = parsed.get("params", {}).get("to")
            if not to_addr or str(to_addr).strip() == "":
                # Try to extract email with regex
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                if emails:
                    parsed["params"]["to"] = emails[0]
                    print(f"DEBUG: Extracted email via regex: {emails[0]}")
                else:
                    print(f"DEBUG: No email found in text: {text}")
        
        print(f"DEBUG: Parsed intent: {parsed}")
        return parsed
    except Exception as e:
        print(f"Error parsing intent: {e}")
        return {"intent": "chat", "params": {"query": text}}

def handle_command(text, chat_id):
    print(f"Routing intent for: {text}")
    parsed = parse_intent(text)
    intent = parsed.get("intent")
    params = parsed.get("params", {})

    # Helper function to show available tools
    def send_help_message():
        help_text = """
🤖 *Available Commands:*

📧 *Communication*
• "Send email to [email]..."
• "Reply to latest email..."
• "Find contact [name]"

📅 *Productivity*
• "Show my calendar"
• "Book meeting tomorrow..."

🎨 *Creation*
• "Write a blog about..."
• "Generate image of..."
• "Make a video about..."
• "Check video status..."

🧠 *Utilities*
• "Search web for..."
• "Weather in [city]"
• "Am I subscribed?"
• "Find image of [query]"

Example: _"Write a blog about AI and send it to me"_
"""
        send_message(chat_id, help_text)

    try:
        if text.strip() == "/help" or text.strip().lower() == "help":
            send_help_message()
            return

        if intent == "calendar_list":
            service = google_calendar.get_service()
            result = google_calendar.list_events(service, max_results=10, date_filter=params.get("date"))
            if result['status'] == 'success':
                events = result['events']
                if not events:
                    send_message(chat_id, f"📅 No events found for {params.get('date') or 'upcoming days'}.")
                else:
                    msg = f"📅 *Schedule ({params.get('date') or 'Upcoming'})*:\n\n"
                    for e in events:
                        t = e['start'].split('T')[1][:5] if 'T' in e['start'] else "All Day"
                        msg += f"• `{t}` - {e['summary']}\n"
                    send_message(chat_id, msg)
            else:
                send_message(chat_id, f"❌ Calendar error: {result['message']}")



        elif intent == "calendar_update":
            target_event_name = params.get("target_event")
            new_start_time = params.get("new_start_time")
            date_filter = params.get("date", "upcoming") # Default to looking at upcoming events
            
            if not target_event_name or not new_start_time:
                 send_message(chat_id, "❌ Please specify which event to move and the new time. Example: 'Reschedule dinner to 7pm'")
                 return

            send_message(chat_id, f"🔍 Looking for event '{target_event_name}' ({date_filter})...")
            
            # 1. Find the event
            service = google_calendar.get_service()
            # We list events for the specific date if provided, or generic list if not
            # Ideally we want to look at "tomorrow" if the user said "tomorrow", or "today"
            # If date_filter is "upcoming" or null, we might need a general search. 
            # list_events default is "upcoming" effectively (timeMin=now).
            
            list_result = google_calendar.list_events(service, max_results=20, date_filter=date_filter if date_filter in ['today', 'tomorrow'] else None)
            
            found_event = None
            if list_result['status'] == 'success':
                events = list_result['events']
                # fuzzy match or substring match
                for e in events:
                    if target_event_name.lower() in e['summary'].lower():
                        found_event = e
                        break
            
            if not found_event:
                 send_message(chat_id, f"❌ Could not find an event matching '{target_event_name}' in {date_filter or 'upcoming events'}.")
            else:
                 # 2. Update the event
                 old_time = found_event['start']
                 formatted_time = old_time.split('T')[1][:5] if 'T' in old_time else old_time
                 send_message(chat_id, f"✅ Found: *{found_event['summary']}* at {formatted_time}. Moving to {new_start_time}...")
                 
                 update_result = google_calendar.update_event(
                     service, 
                     event_id=found_event['id'], 
                     start_time_str=new_start_time
                 )
                 
                 if update_result['status'] == 'success':
                     send_message(chat_id, f"✅ Event Rescheduled: *{found_event['summary']}*\n🔗 [View Event]({update_result.get('link')})")
                 else:
                     send_message(chat_id, f"❌ Update error: {update_result['message']}")



        elif intent == "calendar_delete":
            target_event_name = params.get("target_event")
            date_filter = params.get("date", "upcoming")

            if not target_event_name:
                send_message(chat_id, "❌ Please specify which event to delete. Example: 'Delete dinner'")
                return
            
            send_message(chat_id, f"🔍 Looking for event '{target_event_name}' ({date_filter}) to delete...")

            # 1. Find the event
            service = google_calendar.get_service()
            list_result = google_calendar.list_events(service, max_results=20, date_filter=date_filter if date_filter in ['today', 'tomorrow'] else None)
            
            found_event = None
            if list_result['status'] == 'success':
                events = list_result['events']
                for e in events:
                    if target_event_name.lower() in e['summary'].lower():
                        found_event = e
                        break
            
            if not found_event:
                 send_message(chat_id, f"❌ Could not find an event matching '{target_event_name}' in {date_filter or 'upcoming events'}.")
            else:
                 # 2. Delete the event
                 formatted_time = found_event['start'].split('T')[1][:5] if 'T' in found_event['start'] else found_event['start']
                 
                 delete_result = google_calendar.delete_event(service, event_id=found_event['id'])
                 
                 if delete_result['status'] == 'success':
                     send_message(chat_id, f"🗑️ ✅ Event Cancelled: *{found_event['summary']}* ({formatted_time})")
                 else:
                     send_message(chat_id, f"❌ Delete error: {delete_result['message']}")

        elif intent == "calendar_create":
            service = google_calendar.get_service()
            result = google_calendar.create_event(
                service,
                summary=params.get("summary"),
                start_time_str=params.get("start_time"),
                duration_minutes=params.get("duration", 60),
                description=params.get("description")
            )
            if result['status'] == 'success':
                send_message(chat_id, f"✅ Event created: *{params.get('summary')}*\n🔗 [View Event]({result.get('link')})")
            else:
                send_message(chat_id, f"❌ Calendar error: {result['message']}")

        elif intent == "mail_list":
            service = google_mail.get_service()
            result = google_mail.list_emails(service, max_results=params.get("max_results", 5), query=params.get("query"))
            if result['status'] == 'success':
                emails = result['messages']
                if not emails:
                    send_message(chat_id, "📧 No recent emails found.")
                else:
                    msg = "📧 *Recent Emails*:\n\n"
                    for m in emails:
                        msg += f"From: *{m['from']}*\nSub: {m['subject']}\n`ID: {m['id']}`\n\n"
                    send_message(chat_id, msg)
            else:
                send_message(chat_id, f"❌ Mail error: {result['message']}")

        elif intent == "mail_send":
            to_addr = params.get("to")
            subject = params.get("subject", "(No Subject)")
            body = params.get("body", "")
            
            print(f"DEBUG: Processing mail_send - to={to_addr}, subject={subject}")
            print(f"DEBUG: Full params extracted: {params}")
            
            # Validate that we have a recipient
            if not to_addr or str(to_addr).strip() == "":
                send_message(chat_id, "❌ Cannot send email: No recipient email address found. Please specify who to send the email to (e.g., 'send email to john@example.com')")
            else:
                service = google_mail.get_service()
                result = google_mail.send_email(service, to=to_addr, subject=subject, body=body)
                print(f"DEBUG: mail_send result: {result}")
                if result['status'] == 'success':
                    send_message(chat_id, f"✅ Email sent to *{to_addr}*")
                else:
                    send_message(chat_id, f"❌ Mail error: {result['message']}")

        elif intent == "mail_reply":
            body = params.get("body")
            message_id = params.get("message_id")
            
            if not body:
                send_message(chat_id, "❌ Please specify what to reply. Example: 'reply to latest email: Noted'")
            else:
                service = google_mail.get_service()
                
                # If no message_id, get the latest email
                if not message_id:
                    list_result = google_mail.list_emails(service, max_results=1)
                    if list_result['status'] == 'success' and list_result['messages']:
                        message_id = list_result['messages'][0]['id']
                        print(f"DEBUG: Replying to latest email: {message_id}")
                    else:
                        send_message(chat_id, "❌ No emails found to reply to")
                        return
                
                result = google_mail.reply_email(service, message_id=message_id, body=body)
                print(f"DEBUG: mail_reply result: {result}")
                if result['status'] == 'success':
                    send_message(chat_id, f"✅ Reply sent to email thread")
                else:
                    send_message(chat_id, f"❌ Reply error: {result['message']}")

        elif intent == "mail_draft":
            to_addr = params.get("to")
            subject = params.get("subject", "(No Subject)")
            body = params.get("body", "")
            
            print(f"DEBUG: Processing mail_draft - to={to_addr}, subject={subject}")
            
            if not to_addr or str(to_addr).strip() == "":
                send_message(chat_id, "❌ Cannot create draft: No recipient email address found. Please specify who to send to (e.g., 'draft email to john@example.com')")
            else:
                service = google_mail.get_service()
                result = google_mail.create_draft(service, to=to_addr, subject=subject, body=body)
                print(f"DEBUG: mail_draft result: {result}")
                if result['status'] == 'success':
                    send_message(chat_id, f"✅ Draft created for *{to_addr}*")
                else:
                    send_message(chat_id, f"❌ Draft error: {result['message']}")

        elif intent == "lead_gen":
            query = params.get("query")
            location = params.get("location", "United States")
            limit = params.get("limit", 5)
            
            if not query:
                send_message(chat_id, "❌ Please specify a job title or keyword. Example: 'Find leads for CEO in New York'")
            else:
                send_message(chat_id, f"🔍 Scraping leads for '{query}' in '{location}' (Limit: {limit})...\nThis may take up to a minute.")
                try:
                    leads = scrape_apify.scrape_leads(query, location, limit=limit)
                    if not leads:
                        send_message(chat_id, "❌ No leads found.")
                    else:
                        msg = f"💼 *Leads Found ({len(leads)})*:\n\n"
                        for lead in leads:
                            name = (lead.get('firstName') or '') + ' ' + (lead.get('lastName') or '')
                            company = lead.get('companyName', 'N/A')
                            title = lead.get('jobTitle', 'N/A')
                            email = lead.get('email', 'No Email')
                            linkedin = lead.get('publicIdentifier', None)
                            
                            msg += f"• *{name.strip() or 'Unknown'}*\n"
                            msg += f"  🏢 {company} - {title}\n"
                            msg += f"  📧 {email}\n"
                            if linkedin:
                                msg += f"  🔗 [LinkedIn](https://www.linkedin.com/in/{linkedin})\n"
                            msg += "\n"
                        send_message(chat_id, msg)
                except Exception as e:
                    send_message(chat_id, f"❌ Scraping error: {str(e)}")

        elif intent == "contact_search":
            query = params.get("query")
            if not query:
                send_message(chat_id, "❌ Please specify who to search for. Example: 'Find contact John'")
            else:
                service = google_contacts.get_service()
                result = google_contacts.search_contacts(service, query=query)
                if result['status'] == 'success':
                    contacts = result['contacts']
                    if not contacts:
                        send_message(chat_id, f"👤 No contacts found for '{query}'")
                    else:
                        msg = f"👤 *Contacts Found ({len(contacts)})*:\n\n"
                        for c in contacts[:5]: # Limit to 5
                            msg += f"• *{c['name']}*\n  📧 {c['email']}\n  📞 {c['phone']}\n\n"
                        send_message(chat_id, msg)
                else:
                    send_message(chat_id, f"❌ Contacts error: {result['message']}")

        elif intent == "weather":
            city = params.get("city")
            if not city:
                send_message(chat_id, "❌ Please specify a city. Example: 'Weather in London'")
            else:
                result = weather_agent.get_weather(city)
                if "error" not in result:
                    msg = f"🌤 *Weather in {result['name']}*:\n"
                    msg += f"Temp: {result['main']['temp']}°C\n"
                    msg += f"Conditions: {result['weather'][0]['description'].capitalize()}"
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, f"❌ Weather error: {result['error']}")

        elif intent == "web_search":
            query = params.get("query")
            if not query:
                send_message(chat_id, "❌ Please specify what to search for. Example: 'Search for AI news'")
            else:
                send_message(chat_id, f"🔍 Searching web for '{query}'...")
                result = web_agent.search_web(query)
                if "error" not in result:
                    msg = f"🌐 *Search Results*:\n\n{result.get('ai_summary', 'No summary available.')}"
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, f"❌ Search error: {result['error']}")

        elif intent == "image_gen":
            prompt = params.get("prompt")
            if not prompt:
                send_message(chat_id, "❌ Please describe the image you want to generate. Example: 'Generate an image of a sunset'")
            else:
                send_message(chat_id, f"🎨 Generating image based on: '{prompt}'...")
                result = image_agent.generate_image_workflow(params.get("title", "Telegram Image"), prompt, chat_id)
                if result['status'] == 'success':
                    # image_agent sends the link/image itself if chat_id is provided
                    pass
                else:
                    send_message(chat_id, f"❌ Image error: {result['message']}")

        elif intent == "image_search":
            query = params.get("query")
            if not query:
                send_message(chat_id, "❌ Please specify what image to search for. Example: 'find image of sunset'")
            else:
                send_message(chat_id, f"🔍 Searching for image: '{query}'...")
                result = search_image_agent.search_image(query, intent='search', chat_id=None)
                
                if result.get('status') == 'success':
                    if result.get('result_status') == 'found':
                        msg = f"🖼 *Image Found!*\n\n"
                        msg += f"*Name*: {result.get('image_name')}\n"
                        msg += f"*Drive Link*: [View on Google Drive]({result.get('image_link')})"
                        send_message(chat_id, msg)
                    else:
                        send_message(chat_id, f"❌ No image found for '{query}'")
                else:
                    send_message(chat_id, f"❌ Image search error: {result.get('message', 'Unknown error')}")

        elif intent == "blog_gen":
            topic = params.get("topic")
            audience = params.get("audience", "general audience")
            if not topic:
                send_message(chat_id, "❌ Please specify a topic for the blog. Example: 'Write a blog about AI'")
            else:
                send_message(chat_id, f"📝 Writing blog post about '{topic}' for '{audience}'...\nThis might take a minute.")
                # We pass chat_id to the workflow so it can send the image/text directly
                result = blog_agent.generate_blog_workflow(topic, audience, chat_id=chat_id)
                if result['status'] == 'success':
                     # The agent handles sending the content, we just confirm completion if needed
                     send_message(chat_id, "✅ Blog post workflow completed.")
                else:
                    send_message(chat_id, f"❌ Blog error: {result['message']}")

        elif intent == "video_gen":
            subject = params.get("subject")
            if not subject:
                send_message(chat_id, "❌ Please specify a subject for the video. Example: 'Make a video about cats'")
            else:
                send_message(chat_id, f"🎬 Starting video generation for '{subject}'...")
                result = faceless_video_agent.generate_video_workflow(subject=subject)
                if result['status'] == 'success':
                    msg = f"✅ Video generation started!\nProject ID: `{result.get('project_id')}`\n\nI will notify you when it's ready (or you can ask 'status of video')."
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, f"❌ Video error: {result['message']}")

        elif intent == "video_status":
            project_id = params.get("project_id")
            # If no project ID, we might need to check the last one or all processing ones. 
            # For now, let's just ask for it or check the sheet if we had a state manager.
            # But the agent expects a project_id for status check usually, OR we can implement a 'check all' in agent.
            # Let's assume the agent can handle a missing ID if we look at `faceless_video_agent.py`.
            # Actually, `check_video_status` needs a `project_id`. 
            # We'll rely on the user providing it or manual check for now, or improve later.
            
            if not project_id:
                # Ideally we would track the last project_id in a DB/file. 
                # For now prompt user.
                send_message(chat_id, "ℹ️ Please provide the Project ID. Example: 'Check status of video xyz'")
            else:
                send_message(chat_id, f"Checking status for `{project_id}`...")
                result = faceless_video_agent.check_video_status(project_id)
                if result['status'] == 'success':
                    status = result.get('job_status')
                    video_url = result.get('video_url')
                    if status == 'done':
                        send_message(chat_id, f"✅ Video is READY!\n[Watch Video]({video_url})")
                    else:
                        send_message(chat_id, f"⏳ Video status: {status}")
                else:
                    send_message(chat_id, f"❌ Error checking status: {result['message']}")

        elif intent == "subscription_status":
            email = params.get("email")
            if not email:
                # In a real app we'd map chat_id to email. For now, ask.
                send_message(chat_id, "ℹ️ Please provide the email to check. Example: 'Am I subscribed with test@example.com?'")
            else:
                is_sub = stripe_utils.check_subscription(email)
                if is_sub:
                    send_message(chat_id, f"✅ User {email} is SUBSCRIBED to Premium.")
                else:
                    send_message(chat_id, f"❌ User {email} is NOT subscribed.")
                    # Optionally provide checkout link
                    # link = stripe_utils.create_checkout_session(email, "...", "...")
                    # send_message(chat_id, f"Subscribe here: {link}")

        else: # Default Chat
            # Inject system prompt so the specialized agent knows its own capabilities
            system_prompt = """
            You are an advanced Personal AI Assistant accessible via Telegram.
            
            YOUR CAPABILITIES (Real-time Tools):
            1. Communication: Gmail (Send, Read, Reply), Google Contacts (Search)
            2. Productivity: Google Calendar (List, Create Events)
            3. Creation: Blog Writer (Tavily+OpenAI), Image Gen (DALL-E 3), Video Gen (JSON2Video)
            4. Utilities: Web Search (Tavily), Weather, Stripe Subscription

            CRITICAL INSTRUCTIONS:
            - If the user asks for something listed above, confirm and use the tool (or guide them to the syntax).
            - YouTube/Social Media: You do NOT have direct tools to upload/share to YouTube/Instagram yet. 
              - If asked, say: "I don't have a direct YouTube upload tool installed yet, but I can generate the video content for you using 'Make a video about...'"
              - Do NOT give generic advice on using Buffer/Zapier unless specifically asked for "external tools". 
              - Instead, offer to "Search the web" if they need a tutorial.
            - Ambiguity: If the user says "Share this", ask "Share via Email? I can do that. I cannot share via Social Media yet."
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            response = chat_agent.chat_openai(messages)
            content = response.get('choices', [{}])[0].get('message', {}).get('content', "I'm not sure how to help with that yet.")
            send_message(chat_id, content)

    except Exception as e:
        print(f"Error in handle_command: {e}")
        traceback.print_exc()
        send_message(chat_id, f"⚠️ An error occurred while processing your request: {str(e)}")

def main():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found.")
        return

    print("Telegram Agent started. Listening for messages...")
    last_update_id = None
    
    while True:
        try:
            updates = get_updates(last_update_id)
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    last_update_id = update["update_id"] + 1
                    message = update.get("message")
                    if message:
                        chat_id = str(message["chat"]["id"])
                        text = message.get("text")
                        
                        # Security check: only respond to the configured chat ID
                        if ALLOWED_CHAT_ID and chat_id != str(ALLOWED_CHAT_ID):
                            print(f"Unauthorized access attempt from Chat ID: {chat_id}")
                            continue

                        if text:
                            print(f"Received message: {text}")
                            handle_command(text, chat_id)
                            
            time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
