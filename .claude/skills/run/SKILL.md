---
name: run
description: Run the CyberAssess app locally to see or verify a change working. Use when asked to run, start, or launch CyberAssess, or to confirm a change works in the running app. Triggers on "run/start/launch CyberAssess" and "verify this change in the app".
---

# Running CyberAssess

## Python version — the main trap
**Python 3.13 required.** System Python (3.9) is too old; Homebrew 3.14 breaks Jinja2's `LRUCache`. If 3.13 isn't installed, install it first (`brew install python@3.13`) — don't try to make 3.14 work.

## Setup (first run)
```bash
cp .env.example .env   # add ANTHROPIC_API_KEY
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```
Web portal is Jinja2 + HTMX served by the same FastAPI app.

## Tests
```bash
pytest
```
