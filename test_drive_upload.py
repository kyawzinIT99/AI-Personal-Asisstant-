import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'implementation')))

import image_agent

# Test with a placeholder image
test_url = "https://via.placeholder.com/150"
test_title = "Test Upload"

print("Testing Drive upload...")
result = image_agent.upload_to_drive(test_url, test_title)
print(f"Result: {result}")
