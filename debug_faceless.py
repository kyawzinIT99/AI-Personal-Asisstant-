import os
from dotenv import load_dotenv
load_dotenv()
from implementation import faceless_video_agent

print("Debugging Faceless Video Agent...")
print(f"Sheet ID from Env: {os.getenv('JSON2VIDEO_SHEET_ID')}")
print(f"JSON2Video Key Present: {bool(os.getenv('JSON2VIDEO_API_KEY'))}")
print(f"OpenAI Key Present: {bool(os.getenv('OPENAI_API_KEY'))}")

try:
    # Force read from sheet by passing None
    result = faceless_video_agent.generate_video_workflow(subject=None)
    print("Result:", result)
except Exception as e:
    print("CRITICAL ERROR:", e)
    import traceback
    traceback.print_exc()
