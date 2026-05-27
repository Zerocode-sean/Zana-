import os
from dotenv import load_dotenv

load_dotenv()

# ── Google / Gemini ───────────────────────────────────────────────────────────
GOOGLE_API_KEY         = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT   = os.getenv("GOOGLE_CLOUD_PROJECT")
GEMINI_MODEL           = "gemini-2.0-flash"

# ── WhatsApp Business API ─────────────────────────────────────────────────────
WHATSAPP_API_URL       = "https://graph.facebook.com/v19.0"
WHATSAPP_TOKEN         = os.getenv("WHATSAPP_TOKEN")         # Bearer token
WHATSAPP_PHONE_ID      = os.getenv("WHATSAPP_PHONE_ID")      # Phone number ID
WHATSAPP_VERIFY_TOKEN  = os.getenv("WHATSAPP_VERIFY_TOKEN")  # Webhook verify

# ── Firestore ─────────────────────────────────────────────────────────────────
FIREBASE_CREDENTIALS   = os.getenv("FIREBASE_CREDENTIALS")   # Path to JSON key

# ── Scheduling ────────────────────────────────────────────────────────────────
REMINDER_24HR_HOUR     = 8     # Send 24hr reminders at 8:00 AM
REMINDER_24HR_MINUTE   = 0
DAILY_SUMMARY_HOUR     = 7     # Send daily summary at 7:30 AM
DAILY_SUMMARY_MINUTE   = 30
FOLLOWUP_DELAY_HOURS   = 2     # Follow-up 2 hours after appointment
REPEAT_NUDGE_DAYS      = 30    # Nudge patients after 30 days

# ── Timezone ──────────────────────────────────────────────────────────────────
TIMEZONE               = "Africa/Nairobi"

# ── Conversation ──────────────────────────────────────────────────────────────
MAX_SLOT_OPTIONS       = 3     # Max appointment slots to show patient
UNKNOWN_INTENT_LIMIT   = 3     # Escalate after 3 unknown intents in a row
ESCALATION_TIMEOUT_MIN = 30    # Re-alert owner after 30 min no response
