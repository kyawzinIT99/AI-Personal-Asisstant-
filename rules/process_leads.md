# Process Leads Directive

## Goal
Scrape exactly 10 leads, generate "Spartan" icebreakers, and upload to Google Sheets.

## Required Inputs
- `APIFY_API_TOKEN` in `.env`
- `GOOGLE_SHEETS_ID` in `.env` (Target Spreadsheet)
- `credentials.json` (Service Account)

## Workflow Steps

### 1. Scrape Leads
- **Script**: `implementation/scrape_apify.py`
- **Args**: `--limit 10`
- **Output**: `.tmp/leads_raw.json`
- **Check**: Ensure exactly 10 items (or fewer if not found) are in the JSON.

### 2. Enrich Leads (Icebreakers)
- **Script**: `implementation/enrich_leads.py`
- **Args**: `--input .tmp/leads_raw.json --output .tmp/leads_enriched.json`
- **Output**: `.tmp/leads_enriched.json` containing `icebreaker` field.

### 3. Upload to Sheets
- **Script**: `implementation/upload_sheets.py`
- **Args**: `--input .tmp/leads_enriched.json`
- **Output**: Success message.

## Edge Cases & Recovery
- **Scraper returns 0 leads**: Stop pipeline, alert user.
- **LLM Failure**: If enrichment fails for some leads, skip them or retry (defined in script).
- **Sheet Upload Error**: Check permissions for `credentials.json` service account on the target sheet.
