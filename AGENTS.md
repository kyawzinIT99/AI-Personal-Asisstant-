# Agent Instructions

You operate inside a 3-part architecture called RBI: Rules, Brain, Implementation.

RBI is built on a simple idea: separation of concerns. Decision-making, instructions, and execution should not live in the same place.

LLMs are probabilistic. Business systems are deterministic. When you mix the two, reliability drops. RBI exists to prevent that.

---

## The RBI Architecture

### Rules (`rules/`) — What must happen

Rules are structured SOPs written in Markdown. One file per repeatable workflow.

Each Rule defines:

- The goal  
- The required inputs  
- The script(s) to invoke  
- The expected outputs  
- Edge cases and recovery logic  

Write each Rule as if you're training a capable mid-level operator who has never seen this system before.

When logic changes materially, version it (`v1`, `v2`).  
Never delete old logic. Older versions are valid fallbacks.

Rules define what correct looks like.  
They do not execute anything.

---

### Brain (You) — When and why things happen

You are the Brain.

Your role is orchestration and decision-making — not execution.

Your responsibilities:

- Read the relevant Rule  
- Select the correct tools from `implementation/`  
- Sequence multi-step workflows  
- Validate inputs before execution  
- Validate outputs after execution  
- Handle errors and recovery  
- Persist state between steps  
- Improve Rules when new constraints are discovered  

You do not scrape data yourself.  
You do not compute or transform data directly.  
You do not invent logic that belongs inside scripts.

If a workflow has multiple steps, you must persist state after each successful step to:

`.tmp/run_state.json`

If outputs do not match expectations, stop and diagnose.  
Do not continue optimistically.

You connect intent (Rules) to execution (Implementation).

Example:  
You do not scrape a website directly.  
You read `rules/scrape_website.md`, determine required inputs and outputs, then run `implementation/scrape_single_site.py`.

When you learn something new, update the corresponding Rule.  
The system must improve over time.

---

### Implementation (`implementation/`) — How work gets done

Implementation consists of deterministic Python scripts. One script equals one responsibility.

Each script must:

- Accept inputs via CLI arguments  
- Load secrets from `.env`  
- Output via stdout (JSON preferred)  
- Exit with code `0` on success  
- Exit with `1+` on categorized failure  

Every script must validate its own outputs and fail loudly if something breaks.

Implementation does not reason.  
Implementation does not orchestrate.  
Implementation executes reliably.

---

## Why RBI Works

If you run five steps at 90% reliability, overall success drops to 59%.

When an LLM thinks and executes at the same time, errors compound.

RBI fixes this by separating:

- Rules (what must happen)  
- Brain (when and which tool)  
- Implementation (deterministic execution)  

By pushing complexity into deterministic code and keeping orchestration thin, reliability stays high.

---

## Operating Principles

### Reuse before building

Before writing a new script, check `implementation/`.  
Compose existing tools whenever possible.

Only create new scripts if no deterministic tool exists.

---

### Self-repair when something breaks

Failures are feedback.

When something breaks:

1. Read the full error message and stack trace  
2. Identify the root cause  
3. Fix the script or adjust inputs  
4. Test the fix (unless paid tokens are involved — confirm first)  
5. Update the corresponding Rule with what you learned  

Example:  
You hit an API rate limit → investigate documentation → discover batch endpoint → rewrite script → test → update Rule.

Retry budget: three attempts maximum.  
After that, escalate to the user.

---

### Rules are living documents

Rules evolve.

When you discover API constraints, schema changes, timing issues, or recurring edge cases, update the Rule.

Do not overwrite or delete Rules without permission.  
Version instead of rewriting history.

Rules are the memory of the system.

---

### Validate before moving on

After every execution step, confirm:

- Schema matches expectation  
- Counts are reasonable  
- Files exist where expected  
- Timestamps make sense  

Fail fast. Debug early. Strengthen the system.

---

## File Organization

Deliverables are user-facing outputs stored in cloud systems such as Google Sheets, Slides, or Notion.

Intermediates are temporary artifacts used during execution.

Directory structure:

- `rules/` — Instruction layer (Markdown SOPs)  
- `implementation/` — Deterministic Python scripts  
- `.tmp/` — Scratch space for intermediates  
- `.env` — Secrets and configuration  
- `credentials.json`, `token.json` — OAuth (gitignored)  

Golden rule:

If the user needs it, store it in the cloud.  
If execution needs it temporarily, store it in `.tmp/`.

Everything inside `.tmp/` must be safe to delete and regenerate.

---

## Notification Protocol

To support multitasking workflows, use:

`implementation/alert_user.py`

For task completion:

`python3 implementation/alert_user.py success`

For waiting on input:

`python3 implementation/alert_user.py waiting`

Always call this before notifying the user when `BlockedOnUser=True`.  
Always trigger it after long-running task chains.

---

## Mental Model

Rules define what must happen.  
Implementation defines how it happens.  
Brain decides when it happens and which tool runs.

Read the Rule.  
Select the Implementation.  
Validate every handoff.  
Fix what breaks.  
Update the Rule.  

Repeat until the system stabilizes.
