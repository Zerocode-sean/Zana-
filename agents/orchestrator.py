"""
Zana Orchestrator Agent
───────────────────────
The root brain. Every inbound WhatsApp message flows through here.
Detects intent, reads conversation state, routes to the correct action.
"""

import re

from google import genai

from config.settings import GOOGLE_API_KEY, GEMINI_MODEL, MAX_SLOT_OPTIONS, UNKNOWN_INTENT_LIMIT
from models.schemas import (
    IncomingMessage, Intent, ConversationState, Language, AppointmentStatus,
    Clinic, Patient
)
from database.firestore_client import (
    get_or_create_patient, get_clinic, update_patient,
    set_conversation_state, get_conversation_context,
    increment_unknown_intent, reset_unknown_intent,
    set_patient_language, create_appointment, cancel_appointment, confirm_appointment,
)
from tools.whatsapp_tool import send_message, get_message
from tools.language_tool import detect_language, normalize_language
from tools.availability_tool import (
    get_available_slots, format_slots_list, format_slot, parse_datetime_from_text
)

_genai_client = genai.Client(api_key=GOOGLE_API_KEY)


def _word_in_text(word: str, text: str) -> bool:
    """Check if a word appears as a whole word (for short tokens)."""
    return bool(re.search(rf"\b{re.escape(word)}\b", text))


def _fallback_intent(message: str) -> Intent:
    """Use simple keyword rules when Gemini is unavailable."""
    text = message.lower().strip()

    if any(term in text for term in [
        "chest pain", "shortness of breath", "can't breathe", "cant breathe",
        "emergency", "urgent", "bleeding", "fainting", "severe pain",
        "fever", "high fever", "high temperature", "stroke", "seizure",
    ]):
        return Intent.URGENT_MEDICAL

    # Check reschedule before schedule since "reschedule" contains "schedule"
    if any(term in text for term in [
        "reschedule", "move", "change time", "badilisha", "later",
    ]):
        return Intent.RESCHEDULE

    if any(term in text for term in [
        "book", "appointment", "schedule", "see the doctor", "visit",
        "consultation", "miadi", "panga", "nataka kuja", "slot",
    ]):
        return Intent.BOOK_APPOINTMENT

    # Word-boundary matching for short/ambiguous tokens
    if any(_word_in_text(t, text) for t in ["confirm", "yes", "ndiyo", "ndio", "sawa", "1", "i'll come", "will come"]):
        return Intent.CONFIRM_APPOINTMENT

    if any(_word_in_text(t, text) for t in ["cancel", "no", "sitakuja", "futa", "2", "not coming"]):
        return Intent.CANCEL_APPOINTMENT

    # Multi-word phrases checked before single-word greetings
    if "good morning" in text or "good evening" in text:
        return Intent.GREETING

    if text in ("3",) or any(_word_in_text(t, text) for t in ["hi", "hello", "hey", "habari", "mambo", "sasa"]):
        return Intent.GREETING

    if any(term in text for term in [
        "hours", "time", "open", "close", "remind", "question",
        "price", "cost", "fee", "charge", "how much", "pricing",
        "where", "location", "address", "services", "wapi", "bei",
    ]):
        return Intent.GENERAL_QUERY

    return Intent.UNKNOWN


# ── Intent Detection ──────────────────────────────────────────────────────────

async def detect_intent(message: str) -> Intent:
    """
    Use Gemini to classify the patient's intent.
    Constrained output — only returns an Intent label.
    """
    prompt = (
        "You are an intent classifier for a Kenyan medical clinic assistant.\n"
        "Classify the message below into exactly ONE of these intents:\n\n"
        "BOOK_APPOINTMENT   - wants to book a new appointment\n"
        "CONFIRM_APPOINTMENT - confirming an existing appointment (yes, confirm, 1, ndiyo, sawa)\n"
        "CANCEL_APPOINTMENT  - cancelling an appointment (cancel, 2, sitakuja, futa)\n"
        "RESCHEDULE          - wants to move to a different time (reschedule, 3, badilisha)\n"
        "GENERAL_QUERY       - asking about hours, price, location, services\n"
        "URGENT_MEDICAL      - symptoms, emergencies, medication questions\n"
        "GREETING            - hello, hi, habari, mambo, hey\n"
        "UNKNOWN             - cannot be classified\n\n"
        "Rules:\n"
        "- Handle English, Swahili, Sheng, and mixed language\n"
        "- Any medical/health question = URGENT_MEDICAL\n"
        "- Numeric replies (1, 2, 3) depend on context but classify as CONFIRM, CANCEL, RESCHEDULE\n"
        "- Reply with ONLY the intent label. Nothing else.\n\n"
        f"Message: {message}"
    )
    try:
        response = _genai_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        raw = (response.text or "").strip().upper()
    except Exception:
        # Gemini can be unavailable or quota-limited; keep the chat moving.
        return _fallback_intent(message)

    # Map raw response to Intent enum
    for intent in Intent:
        if intent.value in raw:
            return intent

    return Intent.UNKNOWN


# ── Core Orchestrator ─────────────────────────────────────────────────────────

async def handle_message(msg: IncomingMessage) -> None:
    """
    Main entry point for every inbound patient message.
    Reads state → detects intent → routes to the right handler.
    """
    # ── Load context ──────────────────────────────────────────────────────────
    patient = get_or_create_patient(msg.from_phone, msg.clinic_id)
    clinic  = get_clinic(msg.clinic_id)

    if not clinic:
        return  # Orphaned message — no clinic found

    # ── Detect language for this message ──────────────────────────────────────
    detected_lang = detect_language(msg.message_body)
    # Always update stored language so proactive messages (reminders) match too
    set_patient_language(msg.from_phone, detected_lang)
    patient.language = detected_lang
    # Use the current message's language for the response
    lang = normalize_language(detected_lang)

    # ── Detect intent ─────────────────────────────────────────────────────────
    intent = await detect_intent(msg.message_body)

    # ── URGENT_MEDICAL always escalates regardless of state ───────────────────
    if intent == Intent.URGENT_MEDICAL:
        await _escalate(msg, patient, clinic, lang)
        return

    # ── Un-escalate if patient sends non-urgent message ───────────────────────
    if patient.conversation_state == ConversationState.ESCALATED:
        set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})
        patient.conversation_state = ConversationState.IDLE

    # ── Route based on current conversation state ─────────────────────────────
    state = patient.conversation_state

    # Mid-flow states take priority over intent
    if state == ConversationState.COLLECTING_NAME:
        await _handle_collect_name(msg, patient, clinic, lang)

    elif state == ConversationState.COLLECTING_SERVICE:
        await _handle_collect_service(msg, patient, clinic, lang)

    elif state == ConversationState.COLLECTING_DATETIME:
        await _handle_collect_datetime(msg, patient, clinic, lang)

    elif state == ConversationState.CONFIRMING_BOOKING:
        await _handle_confirm_slot(msg, patient, clinic, lang)

    elif state == ConversationState.AWAITING_REMINDER_RESPONSE:
        await _handle_reminder_response(msg, patient, clinic, lang, intent)

    elif state == ConversationState.COLLECTING_RESCHEDULE:
        await _handle_reschedule_datetime(msg, patient, clinic, lang)

    elif state == ConversationState.POST_VISIT:
        await _handle_followup_response(msg, patient, clinic, lang, intent)

    # IDLE state — fresh intent routing
    elif state == ConversationState.IDLE:
        if intent == Intent.GREETING:
            await _handle_greeting(msg, clinic, lang)

        elif intent == Intent.BOOK_APPOINTMENT:
            await _start_booking(msg, patient, clinic, lang)

        elif intent == Intent.GENERAL_QUERY:
            await _handle_general_query(msg, clinic, lang)

        elif intent == Intent.UNKNOWN:
            count = increment_unknown_intent(msg.from_phone)
            if count >= UNKNOWN_INTENT_LIMIT:
                await _escalate(msg, patient, clinic, lang)
            elif count == 1:
                reply = await _generate_reply(msg.message_body, clinic, lang, patient.name)
                if reply:
                    await send_message(msg.from_phone, reply)
                else:
                    await send_message(
                        msg.from_phone,
                        get_message("unknown", lang, clinic_name=clinic.name)
                    )
            else:
                await send_message(
                    msg.from_phone,
                    get_message("unknown", lang, clinic_name=clinic.name)
                )
        else:
            # If we just asked "Would you like to book?" and they said yes, start booking
            ctx = get_conversation_context(msg.from_phone)
            if ctx.get("expecting_booking") and intent in (Intent.CONFIRM_APPOINTMENT, Intent.BOOK_APPOINTMENT):
                await _start_booking(msg, patient, clinic, lang)
            else:
                await send_message(
                    msg.from_phone,
                    get_message("no_active_appointment", lang)
                )

    # Reset unknown counter on any successful interaction
    if intent != Intent.UNKNOWN:
        reset_unknown_intent(msg.from_phone)


# ── Conversational Response Generation ──────────────────────────────────────

async def _generate_reply(
    patient_message: str,
    clinic: Clinic,
    lang: str,
    patient_name: str | None = None,
) -> str | None:
    """Use Gemini to generate a natural conversational reply."""
    name_part = f"The patient's name is {patient_name}." if patient_name else "We haven't met yet."
    lang_inst = "Respond in English." if lang == "EN" else "Respond in Swahili."
    prompt = (
        f"You are Zana, a warm and friendly virtual assistant at {clinic.name}, a medical clinic.\n"
        f"{name_part}\n"
        f"The patient just said: \"{patient_message}\"\n\n"
        "Respond naturally and warmly, like a real clinic receptionist.\n"
        "Keep it concise (2-3 sentences).\n"
        "Do NOT use numbered lists or menus.\n"
        "Ask an open-ended question to understand what they need.\n"
        f"{lang_inst}"
    )
    try:
        response = _genai_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return response.text.strip()
    except Exception:
        return None


# ── Flow Handlers ─────────────────────────────────────────────────────────────

async def _handle_greeting(msg: IncomingMessage, clinic: Clinic, lang: str) -> None:
    reply = await _generate_reply(msg.message_body, clinic, lang)
    if not reply:
        reply = get_message("greeting", lang, clinic_name=clinic.name)
    await send_message(msg.from_phone, reply)


async def _start_booking(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str) -> None:
    set_conversation_state(msg.from_phone, ConversationState.COLLECTING_NAME, context={})
    await send_message(msg.from_phone, get_message("ask_name", lang))


async def _handle_collect_name(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str) -> None:
    name    = msg.message_body.strip().title()
    context = {"name": name}

    # Build numbered services list
    services = [f"{['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣'][i]} {s}" for i, s in enumerate(clinic.services)]
    services_list = "\n".join(services)

    set_conversation_state(msg.from_phone, ConversationState.COLLECTING_SERVICE, context=context)
    await send_message(
        msg.from_phone,
        get_message("ask_service", lang, name=name, services_list=services_list)
    )


async def _handle_collect_service(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str) -> None:
    context = get_conversation_context(msg.from_phone)
    text    = msg.message_body.strip()

    # Accept numeric choice or text match
    service = None
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(clinic.services):
            service = clinic.services[idx]
    else:
        # Fuzzy match
        for s in clinic.services:
            if text.lower() in s.lower() or s.lower() in text.lower():
                service = s
                break

    if not service:
        await send_message(
            msg.from_phone,
            get_message("ask_service", lang,
                        name=context.get("name", ""),
                        services_list="\n".join(
                            [f"{['1️⃣','2️⃣','3️⃣','4️⃣'][i]} {s}"
                             for i, s in enumerate(clinic.services)]
                        ))
        )
        return

    context["service"] = service
    set_conversation_state(msg.from_phone, ConversationState.COLLECTING_DATETIME, context=context)
    await send_message(msg.from_phone, get_message("ask_datetime", lang))


async def _handle_collect_datetime(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str) -> None:
    context   = get_conversation_context(msg.from_phone)
    date, pref = parse_datetime_from_text(msg.message_body, clinic)

    if date is None:
        await send_message(msg.from_phone, get_message("ask_datetime", lang))
        return

    slots = get_available_slots(clinic, date, pref, MAX_SLOT_OPTIONS)

    if not slots:
        await send_message(msg.from_phone, get_message("no_slots", lang))
        return

    # Store slot options in context for next step
    context["available_slots"] = [s.isoformat() for s in slots]
    context["doctor"] = clinic.doctors[0]  # Default to first doctor (Phase 2: multi-doctor)

    set_conversation_state(msg.from_phone, ConversationState.CONFIRMING_BOOKING, context=context)
    await send_message(
        msg.from_phone,
        get_message("show_slots", lang, slots_list=format_slots_list(slots, lang))
    )


async def _handle_confirm_slot(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str) -> None:
    from datetime import datetime
    context = get_conversation_context(msg.from_phone)
    text    = msg.message_body.strip()
    slots   = context.get("available_slots", [])

    if not slots:
        await send_message(msg.from_phone, get_message("ask_datetime", lang))
        return

    idx = None
    if text.isdigit():
        idx = int(text) - 1

    if idx is None or not (0 <= idx < len(slots)):
        await send_message(
            msg.from_phone,
            get_message("show_slots", lang, slots_list=format_slots_list(
                [datetime.fromisoformat(s) for s in slots], lang
            ))
        )
        return

    chosen_dt = datetime.fromisoformat(slots[idx])
    name      = context.get("name", patient.name or "")
    service   = context.get("service", "General")
    doctor    = context.get("doctor", clinic.doctors[0])

    # Create the appointment record
    create_appointment(
        clinic_id     = clinic.clinic_id,
        patient_phone = msg.from_phone,
        patient_name  = name,
        doctor_name   = doctor,
        service       = service,
        dt            = chosen_dt,
    )

    # Update patient name if we just learned it
    update_patient(msg.from_phone, {"name": name})

    set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})
    await send_message(
        msg.from_phone,
        get_message("booking_confirmed", lang,
                    name=name,
                    date=chosen_dt.strftime("%A, %d %B"),
                    time=chosen_dt.strftime("%I:%M %p"),
                    doctor=doctor,
                    clinic_name=clinic.name)
    )


async def _handle_reminder_response(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str, intent: Intent) -> None:
    context = get_conversation_context(msg.from_phone)
    appt_id = context.get("appointment_id")
    text    = msg.message_body.strip()

    # Normalize: accept "1"/"yes"/"confirm"/"ndiyo" as confirm, etc.
    if text == "1" or intent == Intent.CONFIRM_APPOINTMENT:
        if appt_id:
            confirm_appointment(clinic.clinic_id, appt_id)
        set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})
        await send_message(
            msg.from_phone,
            get_message("confirmed", lang,
                        name=patient.name or "",
                        time=context.get("time", ""))
        )
        # Notify owner
        await send_message(
            clinic.owner_phone,
            f"✅ {patient.name} confirmed their {context.get('time', '')} appointment."
        )

    elif text == "2" or intent == Intent.CANCEL_APPOINTMENT:
        if appt_id:
            cancel_appointment(clinic.clinic_id, appt_id)
        set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})
        await send_message(
            msg.from_phone,
            get_message("cancelled", lang, name=patient.name or "")
        )
        await send_message(
            clinic.owner_phone,
            f"❌ {patient.name} cancelled their {context.get('time', '')} appointment. Slot is now open."
        )

    elif text == "3" or intent == Intent.RESCHEDULE:
        set_conversation_state(msg.from_phone, ConversationState.COLLECTING_RESCHEDULE, context=context)
        await send_message(msg.from_phone, get_message("ask_reschedule", lang))

    else:
        # Ambiguous — ask again
        await send_message(
            msg.from_phone,
            get_message("reminder_24hr", lang,
                        name=patient.name or "",
                        clinic_name=clinic.name,
                        date=context.get("date", ""),
                        time=context.get("time", ""),
                        doctor=context.get("doctor", ""))
        )


async def _handle_reschedule_datetime(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str) -> None:
    context    = get_conversation_context(msg.from_phone)
    date, pref = parse_datetime_from_text(msg.message_body, clinic)

    if date is None:
        await send_message(msg.from_phone, get_message("ask_reschedule", lang))
        return

    slots = get_available_slots(clinic, date, pref, MAX_SLOT_OPTIONS)

    if not slots:
        await send_message(msg.from_phone, get_message("no_slots", lang))
        return

    context["available_slots"] = [s.isoformat() for s in slots]
    set_conversation_state(msg.from_phone, ConversationState.CONFIRMING_BOOKING, context=context)
    await send_message(
        msg.from_phone,
        get_message("show_slots", lang, slots_list=format_slots_list(slots, lang))
    )


async def _handle_followup_response(msg: IncomingMessage, patient: Patient, clinic: Clinic, lang: str, intent: Intent) -> None:
    text = msg.message_body.strip()

    if text == "1":
        set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})

    elif text == "2":
        await _escalate(msg, patient, clinic, lang)

    elif text == "3":
        set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})
        await _start_booking(msg, patient, clinic, lang)

    else:
        set_conversation_state(msg.from_phone, ConversationState.IDLE, context={})


async def _handle_general_query(msg: IncomingMessage, clinic: Clinic, lang: str) -> None:
    """Route common questions — hours, location, services, pricing."""
    text = msg.message_body.lower()

    if any(w in text for w in ["hour", "time", "open", "close", "saa", "wazi"]):
        days  = ", ".join(clinic.working_days)
        reply = (
            f"We're open {days}.\n"
            f"🕗 {clinic.working_hours.start} – {clinic.working_hours.end}\n\n"
            f"Would you like to book an appointment? 😊"
        )
    elif any(w in text for w in ["price", "cost", "fee", "charge", "how much", "pricing", "bei"]):
        reply = (
            f"Pricing depends on the service you need. "
            f"We'd be happy to discuss — could you book a consultation so the doctor can advise you? 😊"
        )
    elif any(w in text for w in ["where", "location", "address", "wapi", "mahali"]):
        reply = clinic.location or (
            f"Please contact {clinic.name} directly for our exact location."
        )
    elif any(w in text for w in ["service", "offer", "treat", "huduma", "nini"]):
        services = "\n".join([f"• {s}" for s in clinic.services])
        reply = f"We offer:\n{services}\n\nWould you like to book? 😊"
    else:
        reply = (
            "Feel free to ask me anything! I can help with:\n"
            "• Booking appointments\n"
            "• Clinic hours and location\n"
            "• Services and pricing\n\n"
            "What would you like to know? 😊"
        )

    # Flag that we just asked if they want to book — next "yes" starts booking
    set_conversation_state(msg.from_phone, ConversationState.IDLE, context={"expecting_booking": True})
    await send_message(msg.from_phone, reply)


async def _escalate(msg: IncomingMessage, patient: Patient | None, clinic: Clinic, lang: str) -> None:
    """Hand the conversation to a human immediately."""
    set_conversation_state(msg.from_phone, ConversationState.ESCALATED)

    # Reassure patient
    await send_message(
        msg.from_phone,
        get_message("escalate_patient", lang)
    )

    # Alert clinic owner with full context
    patient_name  = patient.name if patient else "A patient"
    patient_phone = msg.from_phone
    await send_message(
        clinic.owner_phone,
        f"⚠️ *Action needed*\n\n"
        f"*Patient:* {patient_name}\n"
        f"*Phone:* {patient_phone}\n"
        f"*Message:* \"{msg.message_body}\"\n\n"
        f"I've paused this conversation. Please respond to them directly."
    )
