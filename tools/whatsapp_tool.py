import httpx
from config.settings import WHATSAPP_API_URL, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID


# ── Send a plain text message ─────────────────────────────────────────────────


async def send_message(to: str, body: str) -> dict:
    """
    Send a WhatsApp text message.
    `to` must be in E.164 format: +254712345678
    """
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


# ── Parse incoming webhook payload ────────────────────────────────────────────


def parse_webhook(payload: dict) -> dict | None:
    """
    Extract the useful parts from a WhatsApp Cloud API webhook payload.
    Returns a flat dict or None if this isn't a message event.
    """
    try:
        entry = payload["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignore delivery receipts and read receipts
        if "messages" not in value:
            return None

        message = value["messages"][0]
        contact = value["contacts"][0]

        # We only handle text messages for now
        if message["type"] != "text":
            return None

        return {
            "from_phone": message["from"],  # E.164 format
            "message_body": message["text"]["body"].strip(),
            "message_id": message["id"],
            "name": contact["profile"]["name"],
            "to_phone": value["metadata"]["display_phone_number"],
        }

    except (KeyError, IndexError):
        return None


# ── Pre-built message templates ───────────────────────────────────────────────
# These are the Zana conversation scripts from our design phase.
# EN = English, SW = Swahili

MESSAGES = {
    # ── Greeting ─────────────────────────────────────────────────────────────
    "greeting_EN": (
        "Hello! 👋 Welcome to {clinic_name}. I'm Zana, your virtual assistant.\n\n"
        "How can I help you today?"
    ),
    "greeting_SW": (
        "Habari! 👋 Karibu {clinic_name}. Mimi ni Zana, msaidizi wako.\n\n"
        "Naweza kukusaidia vipi leo?"
    ),
    # ── Booking flow ──────────────────────────────────────────────────────────
    "ask_name_EN": "What's your name?",
    "ask_name_SW": "Jina lako ni nani?",
    "ask_service_EN": (
        "Nice to meet you, {name} 😊\n\n" "What brings you in? We offer:\n" "{services_list}"
    ),
    "ask_service_SW": (
        "Nafurahi kukujua, {name} 😊\n\n" "Unakuja kwa nini? Tunao:\n" "{services_list}"
    ),
    "ask_datetime_EN": (
        "Got it. When would you like to come in?\n\n"
        '(You can say something like "tomorrow morning" or "Friday at 3pm")'
    ),
    "ask_datetime_SW": (
        "Sawa. Ungependa kuja lini?\n\n" '(Unaweza sema kama "kesho asubuhi" au "Ijumaa saa tisa")'
    ),
    "show_slots_EN": (
        "We have these slots available:\n\n" "{slots_list}\n\n" "Which works for you?"
    ),
    "show_slots_SW": ("Tuna nafasi hizi:\n\n" "{slots_list}\n\n" "Lipi linakufaa?"),
    "booking_confirmed_EN": (
        "✅ You're booked, {name}!\n\n"
        "📅 {date}\n"
        "🕐 {time}\n"
        "👨‍⚕️ {doctor}\n"
        "📍 {clinic_name}\n\n"
        "We'll remind you before your visit. Karibu! 🙏"
    ),
    "booking_confirmed_SW": (
        "✅ Umepanga miadi, {name}!\n\n"
        "📅 {date}\n"
        "🕐 {time}\n"
        "👨‍⚕️ {doctor}\n"
        "📍 {clinic_name}\n\n"
        "Tutakukumbusha kabla ya ziara yako. Karibu! 🙏"
    ),
    # ── Reminders ─────────────────────────────────────────────────────────────
    "reminder_24hr_EN": (
        "Hello {name} 👋\n\n"
        "This is a reminder from {clinic_name}.\n\n"
        "You have an appointment tomorrow:\n"
        "📅 {date}\n"
        "🕐 {time}\n"
        "👨‍⚕️ {doctor}\n\n"
        "Please reply:\n"
        "1️⃣ to confirm\n"
        "2️⃣ to cancel\n"
        "3️⃣ to reschedule"
    ),
    "reminder_24hr_SW": (
        "Habari {name} 👋\n\n"
        "Hii ni ukumbusho kutoka {clinic_name}.\n\n"
        "Una miadi kesho:\n"
        "📅 {date}\n"
        "🕐 {time}\n"
        "👨‍⚕️ {doctor}\n\n"
        "Tafadhali jibu:\n"
        "1️⃣ kukubaliana\n"
        "2️⃣ kufuta\n"
        "3️⃣ kubadilisha"
    ),
    "reminder_2hr_EN": (
        "Hi {name} 👋 Quick reminder —\n\n"
        "Your appointment with {doctor} is in 2 hours ({time}).\n\n"
        "See you soon! 🙏"
    ),
    "reminder_2hr_SW": (
        "Habari {name} 👋 Ukumbusho mfupi —\n\n"
        "Miadi yako na {doctor} iko baada ya masaa mawili ({time}).\n\n"
        "Tutaonana hivi karibuni! 🙏"
    ),
    # ── Reminder responses ────────────────────────────────────────────────────
    "confirmed_EN": (
        "✅ Perfect, {name}!\n\n"
        "We'll see you at {time}. Please arrive 5 minutes early.\n\n"
        "Karibu! 🙏"
    ),
    "confirmed_SW": (
        "✅ Vizuri sana, {name}!\n\n"
        "Tutakuona saa {time}. Tafadhali fika dakika 5 mapema.\n\n"
        "Karibu! 🙏"
    ),
    "cancelled_EN": (
        "Understood, {name}. Your appointment has been cancelled.\n\n"
        "Whenever you're ready to book again, just message us here. 🙏"
    ),
    "cancelled_SW": (
        "Sawa, {name}. Miadi yako imefutwa.\n\n"
        "Unapokuwa tayari kupanga tena, tutumie ujumbe hapa. 🙏"
    ),
    "ask_reschedule_EN": "No problem! 😊\n\nWhat day works better for you?",
    "ask_reschedule_SW": "Sawa kabisa! 😊\n\nSiku gani inakufaa zaidi?",
    # ── Follow-up ─────────────────────────────────────────────────────────────
    "followup_EN": (
        "Hi {name} 👋\n\n"
        "Hope your visit with {doctor} went well!\n\n"
        "How are you feeling?\n"
        "1️⃣ Great, thank you\n"
        "2️⃣ I have a follow-up question\n"
        "3️⃣ I need another appointment"
    ),
    "followup_SW": (
        "Habari {name} 👋\n\n"
        "Tunatumahi ziara yako na {doctor} ilikuwa nzuri!\n\n"
        "Unajisikiaje?\n"
        "1️⃣ Vizuri, asante\n"
        "2️⃣ Nina swali la ufuatiliaji\n"
        "3️⃣ Ninahitaji miadi nyingine"
    ),
    # ── Escalation ────────────────────────────────────────────────────────────
    "escalate_patient_EN": (
        "I understand. Let me connect you with the clinic directly. 🙏\n\n"
        "Please hold on for a moment."
    ),
    "escalate_patient_SW": (
        "Naelewa. Acha nikuunganishe na kliniki moja kwa moja. 🙏\n\n" "Tafadhali subiri kidogo."
    ),
    # ── No available slots ────────────────────────────────────────────────────
    "no_slots_EN": (
        "I'm sorry, we don't have available slots on that day. 😔\n\n"
        "Would another day work for you?"
    ),
    "no_slots_SW": ("Samahani, hatuna nafasi siku hiyo. 😔\n\n" "Je, siku nyingine inakufaa?"),
    # ── No active appointment (confirm/cancel/reschedule in IDLE) ──────────────
    "no_active_appointment_EN": (
        "It looks like you don't have any upcoming appointments. "
        "Would you like to book a new one? Just let me know! 😊"
    ),
    "no_active_appointment_SW": (
        "Inaonekana huna miadi yoyote ijayo. " "Ungependa kupanga miadi mpya? Niambie tu! 😊"
    ),
    # ── General fallback ──────────────────────────────────────────────────────
    "unknown_EN": (
        "I didn't quite catch that. 😊\n\n"
        "Could you tell me what you need? I can help with booking an appointment "
        "or answer any questions you have."
    ),
    "unknown_SW": (
        "Sikuelewa vizuri. 😊\n\n"
        "Unaweza kuniambia unachohitaji? Naweza kusaidia kupanga miadi "
        "au kujibu maswali yako."
    ),
}


def get_message(key: str, language: str, **kwargs) -> str:
    """Fetch a message template and fill in variables."""
    template = MESSAGES.get(f"{key}_{language}", MESSAGES.get(f"{key}_EN", ""))
    return template.format(**kwargs)
