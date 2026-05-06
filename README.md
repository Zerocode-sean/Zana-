# Zana 🏥
### Invisible automation infrastructure for Kenya's service businesses.

Zana is a WhatsApp-native AI agent that sits between a clinic and its patients —
managing the entire appointment lifecycle automatically, in Swahili and English,
without the receptionist lifting a finger.

> *Powered by Zana* — patients never see it. Clinics can't live without it.

---

## What Zana Does (Phase 1)

| Feature | Description |
|---|---|
| 📅 Booking | Patients book appointments via WhatsApp conversation |
| ⏰ 24hr Reminder | Automatic reminder the morning before every appointment |
| ✅ Confirmation | Patient confirms, cancels, or reschedules — handled automatically |
| ⏱️ 2hr Nudge | Gentle nudge for unconfirmed patients 2 hours before |
| 👋 Follow-up | Post-visit check-in 2 hours after appointment |
| 📊 Daily Summary | Morning briefing to clinic owner at 7:30 AM |
| 🆘 Escalation | Medical/urgent queries instantly routed to clinic owner |
| 🇰🇪 Language | Automatic English ↔ Swahili ↔ Sheng detection |

---

## Architecture

```
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

---

## Setup

### Prerequisites
- Python 3.11+
- Google Cloud account (for Firestore + Gemini)
- Meta Developer account (for WhatsApp Business API)
- A WhatsApp Business phone number

### 1. Clone and install

```bash
git clone https://github.com/yourname/zana.git
cd zana
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

You need:
- **GOOGLE_API_KEY** — from [Google AI Studio](https://aistudio.google.com)
- **WHATSAPP_TOKEN** — from [Meta Developer Portal](https://developers.facebook.com)
- **WHATSAPP_PHONE_ID** — your WhatsApp Business phone number ID
- **FIREBASE_CREDENTIALS** — service account JSON from Firebase Console

### 3. Register your first clinic

```bash
# Edit scripts/seed_clinic.py with the clinic's real details
python scripts/seed_clinic.py
```

### 4. Expose your local server (for development)

```bash
# Install ngrok: https://ngrok.com
ngrok http 8000
# Copy the HTTPS URL — you'll need it for WhatsApp webhook setup
```

### 5. Configure WhatsApp webhook

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Your App → WhatsApp → Configuration
3. Webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
4. Verify token: same as `WHATSAPP_VERIFY_TOKEN` in your `.env`
5. Subscribe to: `messages`

### 6. Start Zana

```bash
python webhook/server.py
```

---

## Project Structure

```
zana/
├── agents/
│   └── orchestrator.py      # Root agent — intent detection + state routing
├── tools/
│   ├── whatsapp_tool.py     # Send messages + message templates
│   ├── language_tool.py     # EN/SW/Sheng detection
│   └── availability_tool.py # Slot generation + datetime parsing
├── database/
│   └── firestore_client.py  # All Firestore read/write operations
├── models/
│   └── schemas.py           # Pydantic models + enums
├── schedulers/
│   └── trigger_engine.py    # Proactive jobs (reminders, summaries)
├── webhook/
│   └── server.py            # FastAPI server + webhook handler
├── scripts/
│   └── seed_clinic.py       # Register a new clinic
├── config/
│   └── settings.py          # All configuration
├── .env.example             # Environment variables template
└── requirements.txt
```

---

## Conversation States

```
IDLE → COLLECTING_NAME → COLLECTING_SERVICE → COLLECTING_DATETIME
     → CONFIRMING_BOOKING → IDLE

IDLE → AWAITING_REMINDER_RESPONSE → IDLE / COLLECTING_RESCHEDULE

ANY STATE → ESCALATED (on urgent medical query)
```

---

## Roadmap

- **Phase 1** (Now) — Booking, reminders, follow-ups, daily summary
- **Phase 2** — M-Pesa payment confirmation, multi-doctor scheduling, owner dashboard
- **Phase 3** — Multi-clinic, analytics, expand to salons/physio/tutors
- **Phase 4** — Open API for third-party integrations → Zana Platform

---

## Philosophy

> Technology alone is not enough. Zana meets Kenyan businesses where they are —
> on WhatsApp, in Swahili, with the warmth of a person and the precision of a machine.

*Powered by Zana. Built for Africa.*
# Zana-
