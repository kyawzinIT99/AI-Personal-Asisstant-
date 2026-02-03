from flask import Flask, render_template, request, jsonify
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add implementation folder to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'implementation')))

import google_mail
import google_calendar
import generate_mock_leads
import scrape_apify
import web_agent
import chat_agent
import weather_agent
import blog_agent
import image_agent
import search_image_agent
import search_image_agent
import stripe_utils
import faceless_video_agent
import google_contacts
import verify_google_creds
import clickup_agent
from telegram_agent import handle_command, ALLOWED_CHAT_ID, download_telegram_file, transcribe_voice, send_message

app = Flask(__name__)

# Ensure token.json is accessible to the imported modules (they expect it in CWD)
# In this simple setup, we assume server.py is running from the project root.

@app.route('/')
def index():
    return render_template('index.html')

# --- MAIL ENDPOINTS ---

@app.route('/api/mail/list', methods=['GET'])
def list_mail():
    try:
        max_results = request.args.get('max_results', default=10, type=int)
        service = google_mail.get_service()
        result = google_mail.list_emails(service, max_results=max_results)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

@app.route('/api/mail/send', methods=['POST'])
def send_mail():
    data = request.json
    service = google_mail.get_service()
    result = google_mail.send_email(
        service, 
        to=data.get('to'), 
        subject=data.get('subject'), 
        body=data.get('body')
    )
    return jsonify(result)

@app.route('/api/mail/read/<message_id>', methods=['GET'])
def read_mail(message_id):
    service = google_mail.get_service()
    result = google_mail.read_email(service, message_id)
    return jsonify(result)

@app.route('/api/mail/draft', methods=['POST'])
def create_draft():
    data = request.json
    service = google_mail.get_service()
    result = google_mail.create_draft(
        service,
        to=data.get('to'),
        subject=data.get('subject'),
        body=data.get('body')
    )
    return jsonify(result)

@app.route('/api/mail/reply', methods=['POST'])
def reply_mail():
    data = request.json
    service = google_mail.get_service()
    result = google_mail.reply_email(
        service,
        message_id=data.get('message_id'),
        body=data.get('body')
    )
    return jsonify(result)

@app.route('/api/mail/delete/<message_id>', methods=['DELETE'])
def delete_mail(message_id):
    service = google_mail.get_service()
    result = google_mail.delete_email(service, message_id)
    return jsonify(result)

# --- CALENDAR ENDPOINTS ---

@app.route('/api/calendar/list', methods=['GET'])
def list_calendar():
    try:
        max_results = request.args.get('max_results', default=10, type=int)
        service = google_calendar.get_service()
        result = google_calendar.list_events(service, max_results=max_results)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

@app.route('/api/calendar/create', methods=['POST'])
def create_event():
    data = request.json
    service = google_calendar.get_service()
    result = google_calendar.create_event(
        service, 
        summary=data.get('summary'), 
        start_time_str=data.get('start_time'), 
        duration_minutes=data.get('duration_minutes', 60),
        description=data.get('description'),
        attendees=data.get('attendees')
    )
    return jsonify(result)

@app.route('/api/calendar/event/<event_id>', methods=['GET'])
def get_event(event_id):
    service = google_calendar.get_service()
    result = google_calendar.get_event(service, event_id)
    return jsonify(result)

@app.route('/api/calendar/update', methods=['POST'])
def update_event():
    data = request.json
    service = google_calendar.get_service()
    result = google_calendar.update_event(
        service,
        event_id=data.get('event_id'),
        summary=data.get('summary'),
        start_time_str=data.get('start_time'),
        duration_minutes=data.get('duration_minutes'),
        description=data.get('description'),
        attendees=data.get('attendees')
    )
    return jsonify(result)

@app.route('/api/calendar/delete/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    service = google_calendar.get_service()
    result = google_calendar.delete_event(service, event_id)
    return jsonify(result)

# --- LEADS ENDPOINTS ---

@app.route('/api/leads/search', methods=['GET'])
def search_leads():
    query = request.args.get('query', default='CEO')
    location = request.args.get('location', default='United States')
    limit = request.args.get('limit', default=10, type=int)
    mock = request.args.get('mock', default='false').lower() == 'true'

    if mock:
        try:
            leads = generate_mock_leads.get_mock_leads(limit=limit)
            return jsonify({'status': 'success', 'leads': leads})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        try:
            # We aren't passing size/industry/email_status from UI yet, so defaults apply
            leads = scrape_apify.scrape_leads(query=query, location=location, limit=limit)
            return jsonify({'status': 'success', 'leads': leads})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

# --- WEB AGENT ENDPOINTS ---

@app.route('/api/web/search', methods=['GET', 'POST'])
def web_search():
    if request.method == 'POST':
        data = request.json
        query = data.get('query')
    else:
        query = request.args.get('query')
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
        
    result = web_agent.search_web(query)
    return jsonify(result)

# --- CHAT AGENT ENDPOINTS ---

@app.route('/api/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    messages = data.get('messages')
    if not messages:
        return jsonify({'error': 'Messages are required'}), 400
    
    result = chat_agent.chat_openai(messages)
    return jsonify(result)

# --- WEATHER AGENT ENDPOINTS ---

@app.route('/api/weather/current', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
        
    result = weather_agent.get_weather(city)
    return jsonify(result)

# --- BLOG AGENT ENDPOINTS ---

@app.route('/api/blog/generate', methods=['POST'])
def generate_blog():
    data = request.json
    topic = data.get('topic')
    audience = data.get('audience')
    chat_id = data.get('chat_id') # Optional

    if not topic or not audience:
        return jsonify({'error': 'Topic and Audience are required'}), 400

    # Run the workflow
    result = blog_agent.generate_blog_workflow(topic, audience, chat_id)
    return jsonify(result)

# --- IMAGE AGENT ENDPOINTS ---

@app.route('/api/image/generate', methods=['POST'])
def generate_image_api():
    data = request.json
    title = data.get('title', 'Untitled')
    prompt = data.get('prompt')
    chat_id = data.get('chat_id')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    result = image_agent.generate_image_workflow(title, prompt, chat_id)
    return jsonify(result)

# --- IMAGE SEARCH ENDPOINTS ---

@app.route('/api/image/search', methods=['POST'])
def search_image_api():
    data = request.json
    query = data.get('query')
    intent = data.get('intent', 'search')  # 'search' or 'get'
    chat_id = data.get('chat_id')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    result = search_image_agent.search_image(query, intent, chat_id)
    return jsonify(result)

# --- SUBSCRIPTION ENDPOINTS ---

@app.route('/api/subscription/status', methods=['GET'])
def subscription_status():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    is_subscribed = stripe_utils.check_subscription(email)
    price_id = stripe_utils.get_premium_price_id()
    
    return jsonify({
        'status': 'success',
        'subscribed': is_subscribed,
        'email': email,
        'debug_price_id': price_id # For debugging
    })

@app.route('/api/subscription/checkout', methods=['POST'])
def subscription_checkout():
    data = request.json
    email = data.get('email')
    # Use request.host_url to build absolute URLs
    base_url = request.host_url.rstrip('/')
    success_url = f"{base_url}/?subscription=success"
    cancel_url = f"{base_url}/?subscription=canceled"
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    session_url = stripe_utils.create_checkout_session(email, success_url, cancel_url)
    
    if session_url:
        return jsonify({'status': 'success', 'checkout_url': session_url})
    else:
        return jsonify({'status': 'error', 'message': 'Could not create checkout session'}), 500

# --- FACELESS VIDEO ENDPOINTS ---

@app.route('/api/video/generate', methods=['POST'])
def generate_video():
    data = request.json
    subject = data.get('subject')
    email = data.get('email')
    
    
    if not subject:
        return jsonify({'error': 'Subject is required'}), 400
        
    # 2. Start Generation
    result = faceless_video_agent.generate_video_for_subject(subject)
    return jsonify(result)

@app.route('/api/video/status', methods=['GET'])
def video_status():
    project_id = request.args.get('project_id')
    if not project_id:
         return jsonify({'error': 'Project ID is required'}), 400
         
    result = faceless_video_agent.check_video_status(project_id)
    return jsonify(result)

# --- CONTACTS ENDPOINTS ---

@app.route('/api/contacts/list', methods=['GET'])
def list_contacts():
    try:
        max_results = request.args.get('max_results', default=20, type=int)
        service = google_contacts.get_service()
        result = google_contacts.list_contacts(service, max_results=max_results)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

@app.route('/api/contacts/search', methods=['GET'])
def search_contacts():
    try:
        query = request.args.get('q', default='')
        service = google_contacts.get_service()
        result = google_contacts.search_contacts(service, query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401


# --- CLICKUP ENDPOINTS ---

@app.route('/api/clickup/task/<task_id>', methods=['GET'])
def get_clickup_task(task_id):
    result = clickup_agent.get_task(task_id)
    return jsonify(result)

@app.route('/api/clickup/create', methods=['POST'])
def create_clickup_task():
    data = request.json
    list_id = data.get('list_id')
    if not list_id or list_id == "0":
        list_id = os.getenv("CLICKUP_LIST_ID")
        
    name = data.get('name')
    description = data.get('description', '')
    
    if not list_id or not name:
        return jsonify({'error': 'List ID and Name are required (and CLICKUP_LIST_ID is not set in .env)'}), 400
        
    result = clickup_agent.create_task(list_id, name, description)
    return jsonify(result)

@app.route('/api/clickup/list/<list_id>', methods=['GET'])
def list_clickup_tasks(list_id):
    if not list_id or list_id == "0":
        list_id = os.getenv("CLICKUP_LIST_ID")
        
    if not list_id:
         return jsonify({'status': 'error', 'message': 'No List ID provided and CLICKUP_LIST_ID not set.'}), 400

    result = clickup_agent.list_tasks(list_id)
    return jsonify(result)

@app.route('/api/clickup/search', methods=['GET'])
def search_clickup_tasks():
    query = request.args.get('query')
    list_id = request.args.get('list_id') or os.getenv("CLICKUP_LIST_ID")
    if not query:
        return jsonify({"status": "error", "message": "Search query is required."}), 400
    
    if not list_id:
        return jsonify({'status': 'error', 'message': 'No List ID provided and CLICKUP_LIST_ID not set.'}), 400

    result = clickup_agent.search_tasks(list_id, query)
    return jsonify(result)

@app.route('/api/auth/google', methods=['GET'])
def authorize_google():
    try:
        verify_google_creds.main()
        if os.path.exists('token.json'):
            return jsonify({"status": "success", "message": "Authentication successful!"})
        else:
            return jsonify({"status": "error", "message": "Authentication failed or cancelled."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- TELEGRAM WEBHOOK ---

@app.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        # Telegram sends the message in 'message' object
        message = data.get('message')
        if not message:
            return jsonify({"status": "ignored", "message": "No message object"}), 200

        chat_id = str(message.get('chat', {}).get('id'))
        text = message.get('text')
        voice = message.get('voice')

        # Security check: only respond to the configured chat ID
        if ALLOWED_CHAT_ID and chat_id != str(ALLOWED_CHAT_ID):
            print(f"Unauthorized access attempt from Chat ID: {chat_id}")
            return jsonify({"status": "forbidden"}), 403

        if voice:
            print(f"Webhook received voice message from {chat_id}")
            send_message(chat_id, "🎙️ _Transcribing your voice message..._")
            
            file_id = voice["file_id"]
            voice_content = download_telegram_file(file_id)
            
            if voice_content:
                transcribed_text = transcribe_voice(voice_content)
                if transcribed_text:
                    print(f"Transcribed: {transcribed_text}")
                    send_message(chat_id, f"📝 _Transcribed_: \"{transcribed_text}\"")
                    handle_command(transcribed_text, chat_id)
                else:
                    send_message(chat_id, "❌ Sorry, I couldn't transcribe your voice message.")
            else:
                send_message(chat_id, "❌ Sorry, I couldn't download your voice message.")
        
        elif text:
            print(f"Webhook received message: {text}")
            handle_command(text, chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
        traceback_print_exc = traceback.format_exc()
        print(traceback_print_exc)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Run without debug mode to avoid termios/reloader issues in background
    app.run(debug=False, port=5001)
