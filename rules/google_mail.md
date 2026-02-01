---
description: Integration with Google Mail (Gmail) for sending and reading emails.
---

# Google Mail (Gmail) Rule

## Goal
Enable the AI agent to send emails, list recent messages, and read specific email content using the Gmail API.

## Tools
- `implementation/google_mail.py`

## Actions

### 1. Send Email
Send a new email to a recipient.

**Command:**
```bash
python3 implementation/google_mail.py --action send --to "recipient@example.com" --subject "Subject Line" --body "Email body content"
```

**Inputs:**
- `action`: `send`
- `to`: Recipient email address
- `subject`: Email subject
- `body`: Plain text body of the email

**Output (JSON):**
```json
{
  "status": "success",
  "message_id": "18e123456789abc"
}
```

### 2. List Emails
List recent emails from the inbox.

**Command:**
```bash
python3 implementation/google_mail.py --action list --max_results 5
```

**Inputs:**
- `action`: `list`
- `max_results` (optional): Number of emails to return (default: 10)
- `query` (optional): search query (e.g., "is:unread")

**Output (JSON):**
```json
{
  "status": "success",
  "messages": [
    {
      "id": "18e...",
      "snippet": "Hello world...",
      "subject": "Welcome",
      "from": "sender@example.com"
    }
  ]
}
```

### 3. Read Email
Get full content of a specific email.

**Command:**
```bash
python3 implementation/google_mail.py --action read --message_id "18e..."
```

**Inputs:**
- `action`: `read`
- `message_id`: The ID of the message to read

**Output (JSON):**
```json
{
  "status": "success",
  "id": "18e...",
  "subject": "Welcome",
  "from": "sender@example.com",
  "body": "Full body content..."
}
```

## Error Handling
- If `token.json` is missing/invalid, fail and request re-authentication.
- If API error occurs, output JSON with `status: error` and `message`.
