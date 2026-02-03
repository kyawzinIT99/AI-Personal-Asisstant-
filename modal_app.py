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
    .add_local_dir(".", remote_path="/root/app")
    .add_local_file("credentials.json", remote_path="/root/app/credentials.json")
    .add_local_file("token.json", remote_path="/root/app/token.json")
)

# App definition
app = modal.App("personal-ai-assistant")

# Secrets: Read from .env
secrets = [modal.Secret.from_dotenv()]

@app.function(
    image=image,
    secrets=secrets,
    min_containers=1
)
@modal.wsgi_app()
def web_app():
    # Ensure dependencies and imports relative to /root/app work
    import sys
    sys.path.append("/root/app")
    os.chdir("/root/app")
    
    from server import app as flask_app
    return flask_app

if __name__ == "__main__":
    print("Run 'modal deploy modal_app.py' to deploy to the cloud.")
