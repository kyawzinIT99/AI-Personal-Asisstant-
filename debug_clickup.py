import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("CLICKUP_PERSONAL_TOKEN")
list_id = os.getenv("CLICKUP_LIST_ID")

print(f"Using Token: {token[:5]}..." if token else "Token: None")
print(f"Using List ID: {list_id}")

url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

headers = {
    "Authorization": token,
    "Content-Type": "application/json"
}

payload = {
    "name": "Debug Task SU SU (Direct)",
    "description": "If you see this, the API works. Created by verification script."
}

try:
    print(f"Sending POST to {url}...")
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"SUCCESS! Created Task ID: {data.get('id')}")
        print(f"URL: {data.get('url')}")
        print(f"Status: {data.get('status', {}).get('status')}")
        print(f"Assignees: {data.get('assignees')}")
    else:
        print("FAILED to create task.")

except Exception as e:
    print(f"Local Error: {e}")
