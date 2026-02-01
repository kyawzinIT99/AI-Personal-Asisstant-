import os
import json
import argparse
import sys
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def scrape_leads(query, location, limit=10, size=None, industry=None, email_status=None):
    # CONSTANTS
    ACTOR_ID = "IoSHqwTR9YGhzccez"  # The specific actor ID provided
    # HARD LIMIT ENFORCEMENT
    SAFE_LIMIT = 10 # HARDCODED STRICT MAX
    
    if limit > 10:
        print("WARNING: Requested limit > 10. Forcing limit to 10.")
        limit = 10
        
    # Double check safe limit
    if SAFE_LIMIT > 10:
        raise ValueError("CRITICAL SAFETY ERROR: LIMIT > 10")
    
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        raise ValueError("Error: APIFY_API_TOKEN not found in .env")

    print(f"Initializing ApifyClient with strict limit: {SAFE_LIMIT}...")
    print(f"Filters: Query='{query}', Location='{location}', Size='{size}', Industry='{industry}', EmailStatus='{email_status}'")
    client = ApifyClient(api_token)

    # Actor input configuration (MATCHING USER SCHEMA STRICTLY)
    run_input = {
        "fetch_count": SAFE_LIMIT,
        "contact_job_title": [query], 
        "contact_location": [location.lower()], 
    }
    
    # Add optional filters if provided
    if size:
        run_input["size"] = [size]
    if industry:
        run_input["company_industry"] = [industry.lower()]
    if email_status:
        run_input["email_status"] = [email_status.lower()]
    
    try:
        # Start the actor and wait for it to finish
        print(f"Starting actor {ACTOR_ID} run (fetch_count={SAFE_LIMIT})...")
        print(f"Input payload: {json.dumps(run_input, indent=2)}")
        run = client.actor(ACTOR_ID).call(run_input=run_input)
        
        # Fetch results
        dataset_id = run["defaultDatasetId"]
        print(f"Run finished. Fetching results from dataset {dataset_id}...")
        
        items = list(client.dataset(dataset_id).iterate_items(limit=SAFE_LIMIT))
        
        # Enforce limit post-fetch just in case
        items = items[:SAFE_LIMIT]
        return items
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        raise e

def main():
    print("DEBUG: Starting main function...")
    parser = argparse.ArgumentParser(description="Scrape leads using Apify.")
    parser.add_argument("--limit", type=int, default=10, help="Number of leads to scrape (MAX 10 enforced).")
    parser.add_argument("--query", type=str, default="CEO", help="Search query (e.g. 'CEO', 'Founder').")
    parser.add_argument("--location", type=str, default="United States", help="Location filter.")
    parser.add_argument("--size", type=str, default=None, help="Company size (e.g. '51-200').")
    parser.add_argument("--industry", type=str, default=None, help="Industry filter.")
    parser.add_argument("--email-status", type=str, default=None, help="Email status (e.g. 'validated').")
    args = parser.parse_args()

    try:
        items = scrape_leads(
            query=args.query,
            location=args.location,
            limit=args.limit,
            size=args.size,
            industry=args.industry,
            email_status=args.email_status
        )
        
        # Save to .tmp/leads_raw.json
        output_path = ".tmp/leads_raw.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(items, f, indent=2)
            
        print(f"Success: Saved {len(items)} leads to {output_path}")

    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    print("DEBUG: Condition __name__ == '__main__' met.")
    main()
