from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


# ── Enums ─────────────────────────────────────────────────────────────────────


class Language(str, Enum):
    ENGLISH = "EN"
    SWAHILI = "SW"
    SHENG = "SHENG"


class AppointmentStatus(str, Enum):
    BOOKED = "BOOKED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class ConversationState(str, Enum):
    IDLE = "IDLE"
    COLLECTING_NAME = "COLLECTING_NAME"
    COLLECTING_SERVICE = "COLLECTING_SERVICE"
    COLLECTING_DATETIME = "COLLECTING_DATETIME"
    CONFIRMING_BOOKING = "CONFIRMING_BOOKING"
    AWAITING_REMINDER_RESPONSE = "AWAITING_REMINDER_RESPONSE"
    COLLECTING_RESCHEDULE = "COLLECTING_RESCHEDULE"
    ESCALATED = "ESCALATED"
    POST_VISIT = "POST_VISIT"


class Intent(str, Enum):
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    CONFIRM_APPOINTMENT = "CONFIRM_APPOINTMENT"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    RESCHEDULE = "RESCHEDULE"
    GENERAL_QUERY = "GENERAL_QUERY"
    URGENT_MEDICAL = "URGENT_MEDICAL"
    GREETING = "GREETING"
    UNKNOWN = "UNKNOWN"


# ── Core Models ───────────────────────────────────────────────────────────────


class WorkingHours(BaseModel):
    start: str  # "08:00"
    end: str  # "17:00"


class BreakTime(BaseModel):
    start: str  # "13:00"
    end: str  # "14:00"


class Clinic(BaseModel):
    clinic_id: str
    name: str
    doctors: list[str]
    services: list[str]
    working_days: list[str]  # ["Monday","Tuesday"...]
    working_hours: WorkingHours
    break_time: Optional[BreakTime] = None
    slot_duration: int  # minutes (e.g. 30)
    whatsapp_number: str  # The clinic's WA number patients contact
    owner_phone: str  # Owner's personal phone for alerts
    language_preference: Language = Language.ENGLISH
    location: Optional[str] = None


class Patient(BaseModel):
    phone: str  # Primary key — E.164 format e.g. +254712345678
    name: Optional[str] = None
    language: Language = Language.ENGLISH
    clinic_id: Optional[str] = None
    conversation_state: ConversationState = ConversationState.IDLE
    conversation_context: dict = {}  # Stores partial booking data
    unknown_intent_count: int = 0  # Tracks consecutive unknowns
    last_visit: Optional[datetime] = None


class Appointment(BaseModel):
    appointment_id: str
    clinic_id: str
    patient_phone: str
    patient_name: str
    doctor_name: str
    service: str
    datetime_utc: datetime
    status: AppointmentStatus = AppointmentStatus.BOOKED
    reminder_24hr_sent: bool = False
    reminder_2hr_sent: bool = False
    followup_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IncomingMessage(BaseModel):
    """Parsed WhatsApp webhook payload"""

    from_phone: str
    message_body: str
    message_id: str
    timestamp: datetime
    clinic_id: str  # Which clinic this WA number belongs to
