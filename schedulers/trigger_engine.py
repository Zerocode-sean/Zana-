"""
Zana Trigger Engine
────────────────────
The proactive half of Zana. Runs scheduled jobs:
  - 24hr reminders (8:00 AM daily)
  - 2hr reminders  (every 30 minutes)
  - Post-visit follow-ups (every hour)
  - Daily summary to clinic owner (7:30 AM daily)
  - Re-engagement nudges (weekly)

Uses APScheduler for local/Cloud Run deployment.
Swap for Google Cloud Scheduler tasks in production.
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import pytz

from config.settings import (
    TIMEZONE,
    REMINDER_24HR_HOUR, REMINDER_24HR_MINUTE,
    DAILY_SUMMARY_HOUR, DAILY_SUMMARY_MINUTE,
)
from database.firestore_client import (
    get_db,
    get_appointments_for_reminder_24hr,
    get_appointments_for_reminder_2hr,
    get_appointments_for_followup,
    get_todays_appointments,
    update_appointment,
    get_clinic,
)
from database.firestore_client import get_or_create_patient
from models.schemas import ConversationState, AppointmentStatus
from database.firestore_client import set_conversation_state
from tools.whatsapp_tool import send_message, get_message
from tools.language_tool import normalize_language

log = logging.getLogger("zana.triggers")


# ── Helper ────────────────────────────────────────────────────────────────────

def _lang(patient) -> str:
    return normalize_language(patient.language)


# ── Job: 24-hour Reminders ────────────────────────────────────────────────────

async def job_send_24hr_reminders() -> None:
    """
    Runs at 8:00 AM Nairobi time every day.
    Finds all appointments for tomorrow and sends WhatsApp reminders.
    """
    log.info("⏰ Running 24hr reminder job")
    tz  = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    # Fetch all clinics
    clinic_docs = get_db().collection("clinics").stream()

    for clinic_doc in clinic_docs:
        clinic_data = clinic_doc.to_dict()
        clinic_id   = clinic_data["clinic_id"]
        clinic      = get_clinic(clinic_id)
        if not clinic:
            continue

        appointments = get_appointments_for_reminder_24hr(clinic_id)
        log.info(f"  Clinic '{clinic.name}': {len(appointments)} reminders to send")

        for appt in appointments:
            patient = get_or_create_patient(appt.patient_phone, clinic_id)
            lang    = _lang(patient)
            tz_dt   = appt.datetime_utc.astimezone(tz)

            # Send reminder
            await send_message(
                appt.patient_phone,
                get_message(
                    "reminder_24hr", lang,
                    name        = appt.patient_name,
                    clinic_name = clinic.name,
                    date        = tz_dt.strftime("%A, %d %B"),
                    time        = tz_dt.strftime("%I:%M %p"),
                    doctor      = appt.doctor_name,
                )
            )

            # Update appointment + patient state
            update_appointment(clinic_id, appt.appointment_id, {
                "reminder_24hr_sent": True
            })
            set_conversation_state(
                appt.patient_phone,
                ConversationState.AWAITING_REMINDER_RESPONSE,
                context={
                    "appointment_id": appt.appointment_id,
                    "date":   tz_dt.strftime("%A, %d %B"),
                    "time":   tz_dt.strftime("%I:%M %p"),
                    "doctor": appt.doctor_name,
                }
            )

            log.info(f"    ✅ Sent 24hr reminder to {appt.patient_name} ({appt.patient_phone})")


# ── Job: 2-hour Reminders ─────────────────────────────────────────────────────

async def job_send_2hr_reminders() -> None:
    """
    Runs every 30 minutes.
    Sends a gentle nudge to unconfirmed patients 2 hours before their appointment.
    """
    log.info("⏰ Running 2hr reminder job")
    tz = pytz.timezone(TIMEZONE)

    clinic_docs = get_db().collection("clinics").stream()
    for clinic_doc in clinic_docs:
        clinic_id = clinic_doc.to_dict()["clinic_id"]
        clinic    = get_clinic(clinic_id)
        if not clinic:
            continue

        appointments = get_appointments_for_reminder_2hr(clinic_id)
        for appt in appointments:
            patient = get_or_create_patient(appt.patient_phone, clinic_id)
            lang    = _lang(patient)
            tz_dt   = appt.datetime_utc.astimezone(tz)

            await send_message(
                appt.patient_phone,
                get_message(
                    "reminder_2hr", lang,
                    name   = appt.patient_name,
                    doctor = appt.doctor_name,
                    time   = tz_dt.strftime("%I:%M %p"),
                )
            )

            update_appointment(clinic_id, appt.appointment_id, {"reminder_2hr_sent": True})
            log.info(f"    ✅ Sent 2hr reminder to {appt.patient_name}")


# ── Job: Post-Visit Follow-Up ─────────────────────────────────────────────────

async def job_send_followups() -> None:
    """
    Runs every hour.
    Sends a follow-up message 2 hours after each appointment.
    """
    log.info("⏰ Running follow-up job")

    clinic_docs = get_db().collection("clinics").stream()
    for clinic_doc in clinic_docs:
        clinic_id = clinic_doc.to_dict()["clinic_id"]
        clinic    = get_clinic(clinic_id)
        if not clinic:
            continue

        appointments = get_appointments_for_followup(clinic_id)
        for appt in appointments:
            patient = get_or_create_patient(appt.patient_phone, clinic_id)
            lang    = _lang(patient)

            await send_message(
                appt.patient_phone,
                get_message(
                    "followup", lang,
                    name   = appt.patient_name,
                    doctor = appt.doctor_name,
                )
            )

            update_appointment(clinic_id, appt.appointment_id, {
                "followup_sent": True,
                "status": AppointmentStatus.COMPLETED.value,
            })
            set_conversation_state(appt.patient_phone, ConversationState.POST_VISIT)
            log.info(f"    ✅ Sent follow-up to {appt.patient_name}")


# ── Job: Daily Summary to Owner ───────────────────────────────────────────────

async def job_daily_summary() -> None:
    """
    Runs at 7:30 AM Nairobi time every day.
    Sends the clinic owner a summary of today's appointments.
    """
    log.info("⏰ Running daily summary job")
    tz = pytz.timezone(TIMEZONE)

    clinic_docs = get_db().collection("clinics").stream()
    for clinic_doc in clinic_docs:
        clinic_id = clinic_doc.to_dict()["clinic_id"]
        clinic    = get_clinic(clinic_id)
        if not clinic:
            continue

        appointments = get_todays_appointments(clinic_id)
        confirmed    = [a for a in appointments if a.status == AppointmentStatus.CONFIRMED.value]
        pending      = [a for a in appointments if a.status == AppointmentStatus.BOOKED.value]

        if not appointments:
            summary = (
                f"Good morning Dr. 🌅\n\n"
                f"No appointments scheduled for today at {clinic.name}.\n\n"
                f"Have a great day! 🙏"
            )
        else:
            summary = (
                f"Good morning 🌅\n\n"
                f"*{clinic.name} — Today's Schedule*\n\n"
                f"📋 Total appointments: {len(appointments)}\n"
                f"✅ Confirmed: {len(confirmed)}\n"
                f"⏳ Awaiting confirmation: {len(pending)}\n\n"
            )
            if appointments:
                summary += "*Today's patients:*\n"
                for appt in sorted(appointments, key=lambda a: a.datetime_utc):
                    tz_dt  = appt.datetime_utc.astimezone(tz)
                    status = "✅" if appt.status == AppointmentStatus.CONFIRMED.value else "⏳"
                    summary += f"{status} {tz_dt.strftime('%I:%M %p')} — {appt.patient_name} ({appt.service})\n"

            summary += "\nHave a great day! 🙏"

        await send_message(clinic.owner_phone, summary)
        log.info(f"  ✅ Daily summary sent to {clinic.name} owner")


# ── Scheduler Setup ───────────────────────────────────────────────────────────

def create_scheduler() -> AsyncIOScheduler:
    """
    Build and return the configured APScheduler instance.
    Call scheduler.start() in main.py.
    """
    tz        = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # Daily summary — 7:30 AM
    scheduler.add_job(
        job_daily_summary,
        CronTrigger(hour=DAILY_SUMMARY_HOUR, minute=DAILY_SUMMARY_MINUTE, timezone=tz),
        id="daily_summary",
        name="Daily summary to clinic owner",
    )

    # 24hr reminders — 8:00 AM
    scheduler.add_job(
        job_send_24hr_reminders,
        CronTrigger(hour=REMINDER_24HR_HOUR, minute=REMINDER_24HR_MINUTE, timezone=tz),
        id="reminder_24hr",
        name="24hr appointment reminders",
    )

    # 2hr reminders — every 30 minutes
    scheduler.add_job(
        job_send_2hr_reminders,
        "interval",
        minutes=30,
        id="reminder_2hr",
        name="2hr appointment reminders",
    )

    # Follow-ups — every hour
    scheduler.add_job(
        job_send_followups,
        "interval",
        hours=1,
        id="followup",
        name="Post-visit follow-ups",
    )

    return scheduler
