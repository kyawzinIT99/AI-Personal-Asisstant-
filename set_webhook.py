import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MODAL_URL = "https://kyawzin-ccna--personal-ai-assistant-web-app.modal.run"
WEBHOOK_URL = f"{MODAL_URL}/api/telegram/webhook"

if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

def set_webhook():
    print(f"Setting webhook to: {WEBHOOK_URL}")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.post(url, json={"url": WEBHOOK_URL})
    print(f"Result: {response.json()}")

if __name__ == "__main__":
    set_webhook()
