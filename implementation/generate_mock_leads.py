import json
import os
import argparse

def get_mock_leads(limit=10):
    mock_leads = [
        {
            "id": "mock_1",
            "name": "John Doe",
            "first_name": "John",
            "lastName": "Doe",
            "jobTitle": "CEO",
            "company": "TechNova Solutions",
            "company_description": "A leading provider of AI-driven analytics for small businesses.",
            "headline": "CEO at TechNova | AI Enthusiast",
            "location": "San Francisco, CA",
            "linkedInUrl": "https://linkedin.com/in/johndoe",
            "companyUrl": "https://technova.example.com"
        },
        {
            "id": "mock_2",
            "name": "Jane Smith",
            "first_name": "Jane",
            "lastName": "Smith",
            "jobTitle": "Founder",
            "company": "GreenEarth Logistics",
            "company_description": "Sustainable supply chain management and eco-friendly shipping.",
            "headline": "Founder @ GreenEarth | Sustainability Advocate",
            "location": "Austin, Tx",
            "linkedInUrl": "https://linkedin.com/in/janesmith",
            "companyUrl": "https://greenearth.example.com"
        },
        {
            "id": "mock_3",
            "name": "Robert Brown",
            "first_name": "Robert",
            "lastName": "Brown",
            "jobTitle": "Managing Director",
            "company": "Quantum Finance",
            "company_description": "Next-generation high-frequency trading platforms.",
            "headline": "MD at Quantum Finance",
            "location": "New York, NY",
            "linkedInUrl": "https://linkedin.com/in/robertbrown",
            "companyUrl": "https://quantum.example.com"
        }
    ]

    # Repeat list if more items are requested
    final_leads = (mock_leads * (limit // len(mock_leads) + 1))[:limit]
    return final_leads

def main():
    parser = argparse.ArgumentParser(description="Generate mock leads for testing.")
    parser.add_argument("--limit", type=int, default=10, help="Number of mock leads to generate")
    parser.add_argument("--output", default=".tmp/leads_raw.json", help="Output path")
    args = parser.parse_args()

    final_leads = get_mock_leads(args.limit)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(final_leads, f, indent=2)

    print(f"Success: Generated {len(final_leads)} mock leads to {args.output}")

if __name__ == "__main__":
    main()
