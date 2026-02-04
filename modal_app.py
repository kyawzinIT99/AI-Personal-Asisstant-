import modal
import os
import sys

# Define the image
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "flask",
        "requests",
        "python-dotenv",
        "openai",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "gspread",
        "pytelegrambotapi",
        "stripe",
        "apify-client",
        "tavily-python"
    )
    .apt_install("ffmpeg")
    # Selectively add directories to avoid uploading venv/node_modules
    .add_local_dir("implementation", remote_path="/root/app/implementation")
    .add_local_dir("static", remote_path="/root/app/static")
    .add_local_dir("templates", remote_path="/root/app/templates")
    # Core configuration files

    .add_local_file("SOUL.md", remote_path="/root/app/SOUL.md")
    .add_local_file("USER.md", remote_path="/root/app/USER.md")
    .add_local_file("DAILY_JOBS.md", remote_path="/root/app/DAILY_JOBS.md")
    .add_local_file("PERSONAL_EMAIL_RULES.md", remote_path="/root/app/PERSONAL_EMAIL_RULES.md")
    .add_local_file("AGENTS.md", remote_path="/root/app/AGENTS.md")
    
    # Credentials
    .add_local_file("credentials.json", remote_path="/root/app/credentials.json")
    .add_local_file("token.json", remote_path="/root/app/token.json")
    .add_local_file(".env", remote_path="/root/app/.env")
    .add_local_file("server.py", remote_path="/root/app/server.py")
)

# Persistent storage for memory (logs, follow-ups, automation state)
volume = modal.Volume.from_name("personal-ai-memory", create_if_missing=True)

app = modal.App("personal-ai-assistant")
secrets = [modal.Secret.from_dotenv()]

@app.function(
    image=image,
    secrets=secrets,
    volumes={"/root/app/memory": volume},
    timeout=86400, # 24 hours
)
def run_bot():
    """Run the Telegram Bot as a background process."""
    print("Starting Antigravity Telegram Bot...")
    sys.path.append("/root/app")
    os.chdir("/root/app")
    
    from implementation import telegram_agent
    telegram_agent.main()

@app.function(
    image=image,
    secrets=secrets,
    volumes={"/root/app/memory": volume},
)
@modal.wsgi_app()
def web():
    """Run the Flask API."""
    sys.path.append("/root/app")
    os.chdir("/root/app")
    
    from server import app as flask_app
    return flask_app

@app.function(
    image=image,
    secrets=secrets,
    volumes={"/root/app/memory": volume},
    schedule=modal.Period(minutes=15),
)
def automation_trigger():
    """Periodic trigger for morning/evening jobs and urgent alerts."""
    sys.path.append("/root/app")
    os.chdir("/root/app")
    from implementation import telegram_agent
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id:
        print(f"Running scheduled automation check for {chat_id}...")
        telegram_agent.check_automations(str(chat_id))
    else:
        print("TELEGRAM_CHAT_ID not set, skipping automation check.")

if __name__ == "__main__":

    print("Deployment Commands:")
    print("1. Deploy Telegram Bot: modal run modal_app.py::run_bot")
    print("2. Deploy Web App:      modal deploy modal_app.py")


