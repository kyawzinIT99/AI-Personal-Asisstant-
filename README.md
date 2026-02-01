# Personal AI Assistant

A comprehensive AI-powered personal assistant providing a web dashboard for managing emails, calendar events, leads, web research, content generation, and more.

## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)

## Installation

1.  **Clone the repository** (if you haven't already).
2.  **Navigate to the project directory**.
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This project relies on several API keys and configuration files.

### 1. Environment Variables (`.env`)
Create a `.env` file in the root directory and add the following keys:

```ini
# OpenAI (Required for Chat, Image, Blog, etc.)
OPENAI_API_KEY=your_openai_api_key

# Web Search (Required for Web Agent, Blog Agent)
TAVILY_API_KEY=your_tavily_api_key

# Lead Generation (Required for Leads Agent)
APIFY_API_TOKEN=your_apify_api_token
APIFY_SHEETS_ID=optional_apify_sheets_id

# Stripe (Required for Subscription checks)
STRIPE_SECRET_KEY=your_stripe_secret_key

# Weather (Required for Weather Agent)
OPENWEATHER_API_KEY=your_openweather_api_key

# Telegram (Required for sending notifications/images)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Google Sheets IDs (Required for logging and data storage)
GOOGLE_SHEETS_ID=your_main_sheets_id
MARKETING_LOG_SHEETS_ID=your_marketing_log_sheets_id
JSON2VIDEO_SHEET_ID=your_video_generation_sheet_id

# Faceless Video (Required for Video Agent)
JSON2VIDEO_API_KEY=your_json2video_api_key
```

### 2. JSON Configuration Files
Place the following files in the root directory:

*   **`credentials.json`**:
    *   **Purpose**: OAuth 2.0 Client ID for accessing user data (Gmail, Calendar, Drive).
    *   **How to get**: Go to [Google Cloud Console](https://console.cloud.google.com/) -> APIs & Services -> Credentials -> Create Credentials -> OAuth Client ID (Desktop App) -> Download JSON.

*   **`service_account.json`**:
    *   **Purpose**: Service Account Key for server-side operations (like specialized Sheet access if configured).
    *   **How to get**: Go to Google Cloud Console -> IAM & Admin -> Service Accounts -> Create Service Account -> Keys -> Add Key -> Create new key (JSON).

## Google Authentication

Before running the app, you need to authorize it to access your Google account.

1.  Ensure `credentials.json` is in the root folder.
2.  Run the setup script:
    ```bash
    python add_drive_sheets_scopes.py
    ```
3.  A browser window will open. Log in with your Google account and grant the requested permissions.
4.  A `token.json` file will be generated. **Do not delete this file**, as it stores your access session.

### Important: Share Google Sheets
If you are using the **Service Account** (`service_account.json`) for specialized sheet access (like for Faceless Video or specific logs), you MUST share your Google Sheets with the service account email.

1.  Open `service_account.json` and find the `client_email` field.
2.  Copy the email address (e.g., `agent-name@project-id.iam.gserviceaccount.com`).
3.  Open your target Google Sheet (e.g., Marketing Log, Video Plan).
4.  Click the **Share** button in the top right.
5.  Paste the service account email and give it **Editor** access.
6.  Repeat for all Sheets listed in your `.env`.

## Running the Application

1.  Start the local server:
    ```bash
    python server.py
    ```
2.  Open your browser and navigate to:
    ```
    http://127.0.0.1:5001/
    ```

## Dashboard Features

*   **Gmail**: View, send, reply, and delete emails.
*   **Calendar**: View and schedule events.
*   **Leads**: Search for potential leads and mock data generation.
*   **Web Agent**: Perform web searches using Tavily.
*   **Chat Agent**: Chat with an AI assistant.
*   **Weather**: Check current weather for any city.
*   **Blog Post**: Generate blog content based on topics.
*   **Image Gen**: Generate images using DALL-E 3.
*   **Faceless Video**: Generate simple video content from text.