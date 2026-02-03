import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://kyawzin-ccna--personal-ai-assistant-web-app.modal.run/api/telegram/webhook"

def set_webhook():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    
    print(f"Setting webhook to: {WEBHOOK_URL}...")
    response = requests.post(url, json=payload)
    print(response.json())

if __name__ == "__main__":
    set_webhook()
