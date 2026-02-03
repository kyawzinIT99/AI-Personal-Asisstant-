import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.clickup.com/api/v2"

def get_headers():
    token = os.getenv("CLICKUP_PERSONAL_TOKEN")
    if not token:
        print("CRITICAL: CLICKUP_PERSONAL_TOKEN is missing from environment.")
        return None
    return {"Authorization": token}

def get_task(task_id):
    """Fetch task details from ClickUp."""
    headers = get_headers()
    if not headers:
        return {"status": "error", "message": "ClickUp Personal API Token not configured."}
        
    url = f"{BASE_URL}/task/{task_id}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {"status": "success", "task": response.json()}
        else:
            print(f"ClickUp API Error (get_task): {response.status_code} - {response.text}")
            return {"status": "error", "message": f"ClickUp error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_task(list_id, name, description=""):
    """Create a new task in a ClickUp list."""
    headers = get_headers()
    if not headers:
        return {"status": "error", "message": "ClickUp Personal API Token not configured."}
    
    headers["Content-Type"] = "application/json"
    url = f"{BASE_URL}/list/{list_id}/task"
    payload = {
        "name": name,
        "description": description
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return {"status": "success", "task": response.json()}
        else:
            print(f"ClickUp API Error (create_task): {response.status_code} - {response.text}")
            return {"status": "error", "message": f"ClickUp error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_tasks(list_id):
    """List tasks in a ClickUp list."""
    headers = get_headers()
    if not headers:
        return {"status": "error", "message": "ClickUp Personal API Token not configured."}
        
    url = f"{BASE_URL}/list/{list_id}/task"
    
    try:
        print(f"Calling ClickUp list_tasks for ID: {list_id}")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {"status": "success", "tasks": response.json().get('tasks', [])}
        else:
            print(f"ClickUp API Error (list_tasks): {response.status_code} - {response.text}")
            return {"status": "error", "message": f"ClickUp error: {response.status_code} - {response.text}"}
    except Exception as e:
        print(f"Exception in list_tasks: {e}")
        return {"status": "error", "message": str(e)}

def search_tasks(list_id, query):
    """Search for tasks by name in a ClickUp list."""
    headers = get_headers()
    if not headers:
        return {"status": "error", "message": "ClickUp Personal API Token not configured."}
        
    url = f"{BASE_URL}/list/{list_id}/task"
    params = {"search": query}
    
    try:
        print(f"Searching ClickUp tasks in list {list_id} for: {query}")
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return {"status": "success", "tasks": response.json().get('tasks', [])}
        else:
            print(f"ClickUp API Error (search_tasks): {response.status_code} - {response.text}")
            return {"status": "error", "message": f"ClickUp error: {response.status_code} - {response.text}"}
    except Exception as e:
        print(f"Exception in search_tasks: {e}")
        return {"status": "error", "message": str(e)}
