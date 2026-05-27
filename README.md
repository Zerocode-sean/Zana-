# Zana

Invisible automation infrastructure for Kenya's service businesses.

Zana is a WhatsApp-native AI agent that sits between a clinic and its patients,
managing the appointment lifecycle automatically in Swahili and English.

> Powered by Zana. Patients never see it. Clinics do.

## What Zana Does

| Feature | Description |
| --- | --- |
| Booking | Patients book appointments via WhatsApp conversation |
| 24hr Reminder | Automatic reminder the morning before every appointment |
| Confirmation | Patient confirms, cancels, or reschedules automatically |
| 2hr Nudge | Gentle nudge for unconfirmed patients 2 hours before |
| Follow-up | Post-visit check-in 2 hours after appointment |
| Daily Summary | Morning briefing to clinic owner at 7:30 AM |
| Escalation | Medical or urgent queries routed to the clinic owner |
| Language | Automatic English, Swahili, and Sheng detection |

## Architecture

```text
Patient (WhatsApp)
      │
      ▼
WhatsApp Cloud API
      │
      ▼
Zana Webhook (FastAPI)
      │
      ▼
Orchestrator Agent (Gemini)
  ├── Intent Detection
  ├── State Machine
  ├── Booking Flow
  ├── Reminder Response Handler
  └── Escalation Engine
      │
      ▼
Firestore (data layer)
      │
      ▼
WhatsApp Cloud API → Patient / Owner
```

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud account for Firestore and Gemini
- Meta Developer account for WhatsApp Business API
- A WhatsApp Business phone number

### 1. Clone and install

```bash
git clone https://github.com/yourname/zana.git
cd zana
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
```

Set these values in `.env`:

- `GOOGLE_API_KEY` from Google AI Studio
- `WHATSAPP_TOKEN` from Meta Developer Portal
- `WHATSAPP_PHONE_ID` for your WhatsApp Business phone number ID
- `FIREBASE_CREDENTIALS` pointing to your Firebase service account JSON

### 3. Register your first clinic

```bash
python -m scripts.seed_clinic
```

### 4. Expose your local server for development

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL that ngrok prints, for example:

```text
https://abcd-1234.ngrok-free.app
```

Then use this as your callback base URL in WhatsApp:

```text
https://abcd-1234.ngrok-free.app/webhook
```

Keep ngrok and the Zana server running while you test.

### 5. Configure WhatsApp webhook

1. Go to developers.facebook.com
2. Open your app's WhatsApp configuration
3. Set the webhook URL to `https://your-ngrok-url.ngrok.io/webhook`
4. Use the same value as `WHATSAPP_VERIFY_TOKEN` in `.env`
5. Subscribe to `messages`

If the app is still unpublished, WhatsApp will only deliver test webhooks and test-number traffic.
That is expected while you are validating the flow locally.

### 6. Verify the webhook locally before using Meta

```bash
python -m scripts.test_webhook https://abcd-1234.ngrok-free.app/webhook zana_verify_token_123
```

You should see status `200` and body `123456789`. If that fails, Meta will fail too.

### 7. Start Zana

```bash
python run.py
```

## Project Structure

```text
zana/
├── agents/
│   └── orchestrator.py
├── config/
│   └── settings.py
├── database/
│   └── firestore_client.py
├── models/
│   └── schemas.py
├── schedulers/
│   └── trigger_engine.py
├── scripts/
│   └── seed_clinic.py
├── tools/
│   ├── availability_tool.py
│   ├── language_tool.py
│   └── whatsapp_tool.py
├── webhook/
│   └── server.py
├── run.py
├── .env.example
└── requirements.txt
```

## Conversation States

```text
IDLE → COLLECTING_NAME → COLLECTING_SERVICE → COLLECTING_DATETIME
     → CONFIRMING_BOOKING → IDLE

IDLE → AWAITING_REMINDER_RESPONSE → IDLE / COLLECTING_RESCHEDULE

ANY STATE → ESCALATED (on urgent medical query)
```

## Roadmap

- Phase 1: Booking, reminders, follow-ups, daily summary
- Phase 2: M-Pesa payment confirmation, multi-doctor scheduling, owner dashboard
- Phase 3: Multi-clinic, analytics, expand to salons, physio, and tutors
- Phase 4: Open API for third-party integrations

## Philosophy

Technology alone is not enough. Zana meets Kenyan businesses where they are,
on WhatsApp, in Swahili, with the warmth of a person and the precision of a machine.

Powered by Zana. Built for Africa.
