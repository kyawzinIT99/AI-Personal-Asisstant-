import os
import json
import requests
from tavily import TavilyClient
from openai import OpenAI

# Initialize clients
tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

def generate_blog_workflow(topic, audience, chat_id=None):
    """
    Orchestrates the blog post workflow:
    1. Research topic using Tavily
    2. Write blog post using OpenAI
    3. Generate image prompt using OpenAI
    4. Generate image using OpenAI (DALL-E 3)
    5. Send to Telegram (if chat_id is provided)
    """
    try:
        # 1. Research
        print(f"Researching topic: {topic}")
        research_data = research_topic(topic)
        
        # 2. Write Blog Post
        print("Writing blog post...")
        blog_post = write_blog_post(topic, audience, research_data)
        
        # 3. Generate Image Prompt
        print("Generating image prompt...")
        image_prompt_data = create_image_prompt(blog_post)
        image_title = image_prompt_data.get("title", "Blog Image")
        image_prompt = image_prompt_data.get("prompt", f"A professional image representing {topic}")

        # 4. Generate Image
        print(f"Generating image with prompt: {image_prompt}")
        image_url = generate_image(image_prompt)

        # 5. Send to Telegram
        telegram_status = "Skipped (No Chat ID)"
        if chat_id:
            print(f"Sending to Telegram chat ID: {chat_id}")
            telegram_status = send_to_telegram(chat_id, blog_post, image_url)

        return {
            "status": "success",
            "topic": topic,
            "audience": audience,
            "blog_post": blog_post,
            "image_title": image_title,
            "image_prompt": image_prompt,
            "image_url": image_url,
            "telegram_status": telegram_status
        }

    except Exception as e:
        print(f"Error in blog workflow: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def research_topic(topic):
    """Uses Tavily to research the topic."""
    if not tavily_client:
        return "Tavily API key not found. Using mock research."
    
    try:
        response = tavily_client.search(query=topic, search_depth="advanced", max_results=3)
        results = response.get("results", [])
        context = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        return context
    except Exception as e:
        print(f"Tavily search error: {e}")
        return f"Could not research topic due to error: {e}"

def write_blog_post(topic, audience, research_data):
    """Uses OpenAI to write the blog post."""
    if not openai_client:
        return "OpenAI API key not found. Mock blog post."

    system_prompt = """
    You are an AI agent specialized in creating professional, educational, and engaging blog articles.
    
    Objectives:
    - Write a blog post based on the provided topic and research.
    - Appeal to the specified target audience.
    - Start with an engaging intro.
    - Maintain a professional tone.
    - Use headers and subheaders.
    - Include a natural conclusion.
    """
    
    user_prompt = f"""
    Topic: {topic}
    Target Audience: {audience}
    
    Research Context:
    {research_data}
    
    Please write the blog post now.
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # or gpt-4-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI chat error: {e}")
        return f"Error writing blog post: {e}"

def create_image_prompt(blog_post):
    """Generates an image prompt based on the blog post."""
    if not openai_client:
        return {"title": "Mock Title", "prompt": "Mock Prompt"}

    system_prompt = """
    You are an AI agent that transforms blog posts into visual prompt descriptions for generating graphic marketing materials.
    
    Output JSON with two fields:
    1) title (2-4 words)
    2) prompt (The image generation prompt)
    """

    user_prompt = f"""
    Blog Post:
    {blog_post[:2000]}... (truncated)
    
    Generate the JSON for the image prompt.
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI prompt generation error: {e}")
        return {"title": "Error", "prompt": "Abstract representation of the topic"}

def generate_image(prompt):
    """Generates an image using OpenAI DALL-E 3."""
    if not openai_client:
        return "https://via.placeholder.com/1024"

    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"OpenAI image generation error: {e}")
        return "https://via.placeholder.com/1024?text=Error+Generating+Image"

def send_to_telegram(chat_id, text, image_url):
    """Sends the blog post and image to Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return "Telegram Bot Token not configured."

    try:
        # 1. Send Photo
        photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        photo_payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": "Here is the generated image for your blog post."
        }
        requests.post(photo_url, json=photo_payload)

        # 2. Send Text (Blog Post)
        # Telegram has a message limit (4096 chars). We might need to split.
        # For simplicity, we'll send the first 4000 characters or split logic.
        message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Simple chunking
        chunk_size = 4000
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            requests.post(message_url, json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"})
            
        return "Sent successfully"
    except Exception as e:
        print(f"Telegram error: {e}")
        return f"Error sending to Telegram: {e}"
