import uuid
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import pytz

from google.cloud import firestore

from config.settings import FIREBASE_CREDENTIALS, TIMEZONE
from models.schemas import (
    Clinic,
    Patient,
    Appointment,
    ConversationState,
    AppointmentStatus,
    Language,
)

# ── Client singleton ──────────────────────────────────────────────────────────
_db: Optional[firestore.Client] = None


def _normalize_whatsapp_number(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def get_db() -> firestore.Client:
    global _db
    if _db is None:
        credentials_path = Path(FIREBASE_CREDENTIALS or "").expanduser()
        if not credentials_path.is_absolute():
            credentials_path = (Path(__file__).resolve().parents[1] / credentials_path).resolve()

        if not credentials_path.exists():
            raise FileNotFoundError(
                "Firestore credentials file was not found. "
                f"Looked at: {credentials_path}. "
                "Set FIREBASE_CREDENTIALS in .env to a valid JSON key path."
            )

        _db = firestore.Client.from_service_account_json(str(credentials_path))
    return _db


# ── Clinic Operations ─────────────────────────────────────────────────────────


def get_clinic(clinic_id: str) -> Optional[Clinic]:
    doc = get_db().collection("clinics").document(clinic_id).get()  # type: ignore
    if doc.exists:
        data = doc.to_dict()
        return Clinic(**data) if data else None
    return None


def get_clinic_by_whatsapp(whatsapp_number: str) -> Optional[Clinic]:
    """Look up which clinic owns a given WhatsApp number."""
    target = _normalize_whatsapp_number(whatsapp_number)
    docs = get_db().collection("clinics").stream()  # type: ignore
    for doc in docs:
        data = doc.to_dict()
        if not data:
            continue
        clinic = Clinic(**data)
        if _normalize_whatsapp_number(clinic.whatsapp_number) == target:
            return clinic
    return None


# ── Patient Operations ────────────────────────────────────────────────────────


def get_or_create_patient(phone: str, clinic_id: str) -> Patient:
    ref = get_db().collection("patients").document(phone)
    doc = ref.get()  # type: ignore
    if doc.exists:
        data = doc.to_dict()
        return Patient(**data) if data else Patient(phone=phone, clinic_id=clinic_id)

    # First time we see this patient
    patient = Patient(phone=phone, clinic_id=clinic_id)
    ref.set(patient.model_dump())
    return patient


def update_patient(phone: str, updates: dict[str, Any]) -> None:
    get_db().collection("patients").document(phone).update(updates)


def set_conversation_state(
    phone: str, state: ConversationState, context: Optional[dict[str, Any]] = None
) -> None:
    payload: dict[str, Any] = {"conversation_state": state.value}
    if context is not None:
        payload["conversation_context"] = context
    update_patient(phone, payload)


def get_conversation_context(phone: str) -> dict[str, Any]:
    doc = get_db().collection("patients").document(phone).get()  # type: ignore
    if doc.exists:
        data = doc.to_dict()
        return data.get("conversation_context", {}) if data else {}
    return {}


def set_patient_language(phone: str, language: Language) -> None:
    update_patient(phone, {"language": language.value})


def increment_unknown_intent(phone: str) -> int:
    ref = get_db().collection("patients").document(phone)
    doc = ref.get()
    data = doc.to_dict() if doc.exists else {}
    count = data.get("unknown_intent_count", 0) + 1
    ref.update({"unknown_intent_count": count})
    return count


def reset_unknown_intent(phone: str) -> None:
    update_patient(phone, {"unknown_intent_count": 0})


# ── Appointment Operations ────────────────────────────────────────────────────


def create_appointment(
    clinic_id: str,
    patient_phone: str,
    patient_name: str,
    doctor_name: str,
    service: str,
    dt: datetime,
) -> Appointment:
    appt_id = str(uuid.uuid4())
    appt = Appointment(
        appointment_id=appt_id,
        clinic_id=clinic_id,
        patient_phone=patient_phone,
        patient_name=patient_name,
        doctor_name=doctor_name,
        service=service,
        datetime_utc=dt,
    )
    (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .document(appt_id)
        .set(appt.model_dump())
    )
    return appt


def get_appointment(clinic_id: str, appointment_id: str) -> Optional[Appointment]:
    doc = (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .document(appointment_id)
        .get()  # type: ignore
    )
    if doc.exists:
        data = doc.to_dict()
        return Appointment(**data) if data else None
    return None


def update_appointment(clinic_id: str, appointment_id: str, updates: dict[str, Any]) -> None:
    (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .document(appointment_id)
        .update(updates)
    )


def cancel_appointment(clinic_id: str, appointment_id: str) -> None:
    update_appointment(clinic_id, appointment_id, {"status": AppointmentStatus.CANCELLED.value})


def confirm_appointment(clinic_id: str, appointment_id: str) -> None:
    update_appointment(clinic_id, appointment_id, {"status": AppointmentStatus.CONFIRMED.value})


def _docs_to_appointments(docs: Any) -> list[Appointment]:
    """Convert Firestore doc stream to list of Appointments."""
    appointments = []
    for d in docs:
        data = d.to_dict()
        if data:
            appointments.append(Appointment(**data))
    return appointments


def get_appointments_for_reminder_24hr(clinic_id: str) -> list[Appointment]:
    """All BOOKED appointments happening tomorrow that haven't been reminded yet."""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    docs = (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .where("status", "in", [AppointmentStatus.BOOKED.value])
        .where("reminder_24hr_sent", "==", False)
        .where("datetime_utc", ">=", start)
        .where("datetime_utc", "<", end)
        .stream()  # type: ignore
    )
    return _docs_to_appointments(docs)


def get_appointments_for_reminder_2hr(clinic_id: str) -> list[Appointment]:
    """Unconfirmed appointments in the next 2 hours without a 2hr reminder sent."""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    end = now + timedelta(hours=2)

    docs = (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .where("status", "==", AppointmentStatus.BOOKED.value)
        .where("reminder_2hr_sent", "==", False)
        .where("datetime_utc", ">=", now)
        .where("datetime_utc", "<=", end)
        .stream()  # type: ignore
    )
    return _docs_to_appointments(docs)


def get_appointments_for_followup(clinic_id: str) -> list[Appointment]:
    """Completed/past appointments from 2 hours ago without a followup sent."""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    start = now - timedelta(hours=3)
    end = now - timedelta(hours=2)

    docs = (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .where("followup_sent", "==", False)
        .where("datetime_utc", ">=", start)
        .where("datetime_utc", "<=", end)
        .stream()  # type: ignore
    )
    return _docs_to_appointments(docs)


def get_todays_appointments(clinic_id: str) -> list[Appointment]:
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    docs = (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .where("datetime_utc", ">=", start)
        .where("datetime_utc", "<", end)
        .where("status", "!=", AppointmentStatus.CANCELLED.value)
        .stream()  # type: ignore
    )
    return _docs_to_appointments(docs)


def get_booked_slots(clinic_id: str, date: datetime) -> list[datetime]:
    """All booked datetime slots for a given day."""
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    docs = (
        get_db()
        .collection("clinics")
        .document(clinic_id)
        .collection("appointments")
        .where("status", "in", [AppointmentStatus.BOOKED.value, AppointmentStatus.CONFIRMED.value])
        .where("datetime_utc", ">=", start)
        .where("datetime_utc", "<", end)
        .stream()  # type: ignore
    )
    appointments = _docs_to_appointments(docs)
    return [appt.datetime_utc for appt in appointments]
