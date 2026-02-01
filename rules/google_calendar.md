---
description: Integration with Google Calendar for listing and creating events.
---

# Google Calendar Rule

## Goal
Enable the AI agent to list upcoming calendar events and schedule new events (meetings, reminders) using the Google Calendar API.

## Tools
- `implementation/google_calendar.py`

## Actions

### 1. List Events
List upcoming events from the primary calendar.

**Command:**
```bash
python3 implementation/google_calendar.py --action list --max_results 5
```

**Inputs:**
- `action`: `list`
- `max_results` (optional): Number of events to return (default: 10)

**Output (JSON):**
```json
{
  "status": "success",
  "events": [
    {
      "id": "event_id_123",
      "summary": "Team Meeting",
      "start": "2023-10-27T10:00:00-07:00",
      "end": "2023-10-27T11:00:00-07:00"
    }
  ]
}
```

### 2. Create Event
Create a new event on the primary calendar.

**Command:**
```bash
python3 implementation/google_calendar.py --action create --summary "Meeting with Client" --start_time "2023-10-28T14:00:00" --duration_minutes 60
```

**Inputs:**
- `action`: `create`
- `summary`: Event title
- `start_time`: Start time in ISO format (e.g., `YYYY-MM-DDTHH:MM:SS`)
- `duration_minutes`: Length of the event in minutes (default: 60)
- `description` (optional): Description of the event

**Output (JSON):**
```json
{
  "status": "success",
  "event_id": "new_event_id_456",
  "link": "https://www.google.com/calendar/event?eid=..."
}
```

## Error Handling
- If `token.json` is missing/invalid, fail and request re-authentication.
- Ensure `start_time` is valid ISO format.
- If API error occurs, output JSON with `status: error`.
