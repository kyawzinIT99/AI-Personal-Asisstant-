import json
import argparse
import sys
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_icebreaker(lead_data, client):
    """
    Generates a Spartan-style icebreaker using OpenAI.
    """
    # Updated to check for first_name (snake_case) as seen in Apify raw output
    name = lead_data.get("first_name") or lead_data.get("firstName") or lead_data.get("name") or "there"
    company = lead_data.get("company", "your company")
    # Using the scraped description as the core source of truth
    description = lead_data.get("company_description") or lead_data.get("headline") or "Unknown"
    
    prompt = f"""
    We’ve just scraped a set of web pages for a business called {company}. Your task is to turn those summaries into short, personalized, catchy and scroll-stopping openers for a cold email, signaling that the rest of the campaign is tailored as well.

    Rules:
    - Write keeping the tone spartan, direct and laconic.
    - Follow the structure below exactly when constructing the icebreaker; it’s intentional, and needs to be reflected like that
    - Shorten the company name wherever possible (say, "XYZ" instead of "XYZ Agency"). More examples: "Love GIN" instead of "Love GIN Recruitment Services", "Love OBS" instead of "Love OBS LLC.", etc.
    - When filling variables, pull from small, non-obvious details. The goal is to signal real research, not surface-level praise. Avoid generic lines like “Love your website” or “Love your LinkedIn post” or “Love your take on recrutiment” or "Love CompanyName". All variables need to be non-obvious
    - Do the same with locations. "San Fran" instead of "San Francisco", "BC" instead of "British Columbia", etc.
    - Ensure you scraped the website pages in order to actually have the info to add.

    Structure:
    "Hey {name},\\n\\nLove [thing], also into [otherThing]. Wanted to run something by you.\\n\\nHope you don’t mind, but I spent some time looking through you/your site and noticed that [anotherThing] seems important to you guys (or at least that’s how it came across given the focus on [onemoreThing]).\\n\\nI put something together a while ago that I thought might help.\\n\\nLong story short, it’s an outreach system that uses AI to find and qualify candidates based on live hiring signals, then reaches out with personalised messages instead of generic blasts.\\n\\nIt costs just a few cents to run, converts well, and feels aligned with [underlyingBeliefTheySeemToHaveFOundOnWebsiteOrLinkedInPosts]."

    Raw Company Data:
    {json.dumps(lead_data, default=str)[:1500]} 

    Output ONLY the JSON object with the "icebreaker" key containing the generated text.
    Example:
    {{
      "icebreaker": "Hey John,..."
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a concise, elite sales copywriter. Output validation-ready JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=300,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content).get("icebreaker", "")
    except Exception as e:
        print(f"Error generating for {name}: {e}")
        return "ERROR_GENERATING_ICEBREAKER"

def main():
    parser = argparse.ArgumentParser(description="Enrich leads with icebreakers using OpenAI.")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        sys.exit(1)
        
    client = OpenAI(api_key=api_key)

    try:
        with open(args.input, "r") as f:
            leads = json.load(f)
            
        print(f"Loaded {len(leads)} leads. Generating icebreakers...")
        
        enriched_leads = []
        for lead in leads:
            if "icebreaker" in lead:
                enriched_leads.append(lead)
                continue
                
            icebreaker = generate_icebreaker(lead, client)
            lead["icebreaker"] = icebreaker
            enriched_leads.append(lead)
            print(f"Generated for {lead.get('name', 'Lead')}")
            
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(enriched_leads, f, indent=2)
            
        print(f"Success: Enriched leads saved to {args.output}")

    except Exception as e:
        print(f"Fatal error during enrichment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
