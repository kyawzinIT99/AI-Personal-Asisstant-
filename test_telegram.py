import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add implementation folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'implementation')))

import blog_agent

chat_id = os.getenv("TELEGRAM_CHAT_ID")
if not chat_id:
    print("Error: TELEGRAM_CHAT_ID not found in .env")
    sys.exit(1)

print(f"Testing Telegram with Chat ID: {chat_id}")

# Mock data to avoid expensive API calls for just testing Telegram
test_blog = "This is a test blog post from the verification script."
test_image = "https://via.placeholder.com/150"

print("Sending test message...")
result = blog_agent.send_to_telegram(chat_id, test_blog, test_image)
print(f"Result: {result}")
