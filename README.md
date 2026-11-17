# Horizon Properties Desk

Bilingual (English + Arabic) real estate lead qualifier and auto-scheduler for the GCC (Dubai, Saudi Arabia, Qatar, Kuwait), built from the V2.0 technical specification. It ships with a chat app UI where every conversation, the lead profile and the owner calendar live in one screen, plus a WhatsApp webhook that drives the same agent.

## Quick start

```
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:8000 and start chatting. Run the tests with:

```
python -m unittest discover -s tests -t .
```

## What it does

- Detects English or Arabic on every message and replies in the same language (Khaleeji-style Arabic).
- Qualifies the lead on market, purpose, budget (normalised to USD) and timeline, in any order the lead provides them.
- Answers fee, residency and ownership questions from a curated knowledge base. When it has no verified answer it says so and defers to the consultant instead of guessing.
- Offers the next three open 30-minute slots, books the chosen one and prevents double booking.
- Keeps all conversations, lead data and bookings in SQLite.

## Project layout

```
app/
  main.py            Starlette application and routes
  config.py          Settings and environment variables
  service.py         Conversation service and API views
  store.py           SQLite persistence
  dedupe.py          Message id deduplication (TTL)
  agent/
    state.py         Session state (GCCRealEstateState)
    graph.py         Small async state-machine engine
    nodes.py         Agent nodes (ingest, extract, dispatch, faq, qualify, slots)
    pipeline.py      Graph wiring
    extractor.py     Country, intent, budget, timeline, name and slot parsing
    responses.py     English and Arabic reply templates
    language.py      Language detection and Arabic normalisation
  tools/
    calendar.py      Slot lookup and booking
    knowledge.py     Fees, residency and ownership knowledge base
  api/
    chat.py          REST endpoints for the chat app
    whatsapp.py      Webhook verification, signature check, deduplication
    whatsapp_client.py  Outbound WhatsApp Cloud API sender
static/              Chat app (index.html, style.css, app.js)
tests/               Unit and conversation-flow tests
```

## WhatsApp

Set these environment variables and point the Meta webhook at `/whatsapp/webhook`:

| Variable | Purpose |
| --- | --- |
| `WHATSAPP_VERIFY_TOKEN` | Token used for the webhook verification handshake |
| `WHATSAPP_APP_SECRET` | Enables `X-Hub-Signature-256` verification |
| `WHATSAPP_ACCESS_TOKEN` | Cloud API token used to send replies |
| `WHATSAPP_PHONE_NUMBER_ID` | Sending phone number id |

The webhook returns immediately, skips repeated message ids and processes replies in a background task.

## Production notes

This build uses components that need no external services. To match the full architecture in the specification, swap in:

- Redis for message id deduplication in `app/dedupe.py` (the `claim` method is the only interface).
- Google Calendar or Cal.com in `app/tools/calendar.py` (keep `get_slot_options` and `create_calendar_event`).
- Qdrant retrieval in `app/tools/knowledge.py` (keep `detect_topic` and `answer`).
- An LLM-backed extractor in `app/agent/extractor.py` if free-form understanding beyond keyword rules is needed.
- Review the knowledge base figures with a licensed professional before going live. Rules change.

The assistant answers honestly if someone asks whether they are talking to a bot or a person.
