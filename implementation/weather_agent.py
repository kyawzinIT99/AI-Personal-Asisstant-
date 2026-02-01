import os
import requests
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return None
    return OpenAI(api_key=api_key)

def extract_city(query):
    """
    Extract city name from a natural language query using OpenAI.
    """
    client = get_openai_client()
    if not client:
        return query # Fallback to original query
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract the city name from the user's query. Return ONLY the city name. If no city is found, return the original query."},
                {"role": "user", "content": query}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error extracting city with OpenAI: {e}")
        return query

def get_weather(city_query, units="metric"):
    """
    Get current weather for a city using OpenWeatherMap API, with smart city extraction.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        logger.error("OPENWEATHER_API_KEY not found in environment variables")
        return {"error": "OpenWeatherMap API key not configured"}
    
    # Extract clean city name if query looks like a sentence (contains spaces)
    if " " in city_query.strip():
        city_name = extract_city(city_query)
        logger.info(f"Extracted city '{city_name}' from query '{city_query}'")
    else:
        city_name = city_query

    params = {
        "q": city_name,
        "appid": api_key,
        "units": units
    }
    
    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params)
        
        # If 404 and we haven't tried extraction yet (e.g. single word query that failed), try extraction
        if response.status_code == 404 and city_name == city_query and " " not in city_query:
             # It might be a single word that isn't a city but implies one, or just a typo. 
             # For now, let's just return the error, but we could add more logic here.
             pass

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
             return {"error": f"City '{city_name}' not found. Please check spelling."}
        logger.error(f"Error calling OpenWeatherMap API: {e}")
        return {"error": str(e)}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OpenWeatherMap API: {e}")
        return {"error": str(e)}
