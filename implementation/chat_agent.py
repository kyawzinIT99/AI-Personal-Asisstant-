import os
from openai import OpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return None
    return OpenAI(api_key=api_key)

def chat_openai(messages, model="gpt-4o-mini"):
    """
    Chat with OpenAI API.
    """
    client = get_openai_client()
    if not client:
        return {"error": "OpenAI API key not configured"}
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )
        # Return in a format compatible with the frontend expectation (mimicking the previous structure or standard OpenAI response)
        # The frontend expects { "choices": [ { "message": { "content": "..." } } ] } which is standard OpenAI format.
        # The client.chat.completions.create returns an object, we need to serialize it or extract data.
        
        return completion.model_dump()
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return {"error": str(e)}
