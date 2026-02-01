import os
from tavily import TavilyClient
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not found in environment variables")
        return None
    return TavilyClient(api_key=api_key)

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return None
    return OpenAI(api_key=api_key)

def search_web(query, max_results=5, include_answer=True):
    """
    Search the web using Tavily API and summarize with OpenAI.
    """
    tavily = get_tavily_client()
    if not tavily:
        return {"error": "Tavily API key not configured"}
    
    try:
        # Performing the search
        response = tavily.search(
            query=query, 
            search_depth="basic", 
            max_results=max_results,
            include_answer=include_answer
        )
        
        # Summarize with OpenAI
        openai = get_openai_client()
        if openai:
            try:
                context = response.get('results', [])
                # Create a concise context string
                context_str = "\n".join([f"Source: {r['title']}\nContent: {r['content']}" for r in context])
                
                completion = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful research assistant. Summarize the following search results to answer the original query. Be concise."},
                        {"role": "user", "content": f"Query: {query}\n\nSearch Results:\n{context_str}"}
                    ]
                )
                
                summary = completion.choices[0].message.content
                response['ai_summary'] = summary
            except Exception as e:
                logger.error(f"Error summarizing with OpenAI: {e}")
                response['ai_summary'] = "Could not generate summary due to an error."
        else:
             logger.warning("OPENAI_API_KEY not found, skipping summarization")

        return response
    except Exception as e:
        logger.error(f"Error searching web: {e}")
        return {"error": str(e)}
