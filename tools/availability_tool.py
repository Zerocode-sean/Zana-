from datetime import datetime, timedelta
from typing import Optional
import pytz
import re

from config.settings import TIMEZONE
from models.schemas import Clinic
from database.firestore_client import get_booked_slots


# ── Slot generation ───────────────────────────────────────────────────────────

def generate_slots(clinic: Clinic, date: datetime) -> list[datetime]:
    """
    Generate all possible appointment slots for a given day,
    respecting working hours, break time, and slot duration.
    """
    tz     = pytz.timezone(TIMEZONE)
    day_name = date.strftime("%A")   # "Monday", "Tuesday", etc.

    if day_name not in clinic.working_days:
        return []

    start_h, start_m = map(int, clinic.working_hours.start.split(":"))
    end_h,   end_m   = map(int, clinic.working_hours.end.split(":"))

    current = date.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end_dt  = date.replace(hour=end_h,   minute=end_m,   second=0, microsecond=0)

    slots = []
    while current < end_dt:
        # Skip break time
        if clinic.break_time:
            bh, bm = map(int, clinic.break_time.start.split(":"))
            eh, em = map(int, clinic.break_time.end.split(":"))
            break_start = date.replace(hour=bh, minute=bm, second=0, microsecond=0)
            break_end   = date.replace(hour=eh, minute=em, second=0, microsecond=0)
            if break_start <= current < break_end:
                current = break_end
                continue

        slots.append(current)
        current += timedelta(minutes=clinic.slot_duration)

    return slots


def get_available_slots(
    clinic: Clinic,
    date: datetime,
    time_preference: Optional[str] = None,
    max_results: int = 3,
) -> list[datetime]:
    """
    Return available (not yet booked) slots for a date.
    Optionally filter by time preference ('morning', 'afternoon', 'evening').
    Returns at most max_results options.
    """
    tz   = pytz.timezone(TIMEZONE)
    now  = datetime.now(tz)
    date = date.astimezone(tz)

    all_slots    = generate_slots(clinic, date)
    booked_slots = get_booked_slots(clinic.clinic_id, date)

    # Filter out past slots (for today) and already booked ones
    available = [
        s for s in all_slots
        if s > now and s not in booked_slots
    ]

    # Apply time-of-day preference filter
    if time_preference:
        pref = time_preference.lower()
        if "morning" in pref or "asubuhi" in pref:
            available = [s for s in available if s.hour < 12]
        elif "afternoon" in pref or "mchana" in pref or "alasiri" in pref:
            available = [s for s in available if 12 <= s.hour < 17]
        elif "evening" in pref or "jioni" in pref:
            available = [s for s in available if s.hour >= 17]

    return available[:max_results]


def format_slot(dt: datetime, language: str = "EN") -> str:
    """Human-friendly slot display."""
    tz   = pytz.timezone(TIMEZONE)
    dt   = dt.astimezone(tz)
    time = dt.strftime("%I:%M %p")  # "10:00 AM"
    date = dt.strftime("%A, %d %B") # "Tuesday, 14 May"
    return f"{date} at {time}"


def format_slots_list(slots: list[datetime], language: str = "EN") -> str:
    """
    Format a numbered list of slots for WhatsApp display.
    1️⃣ Tuesday, 14 May at 10:00 AM
    2️⃣ Tuesday, 14 May at 11:30 AM
    """
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    lines  = [f"{emojis[i]} {format_slot(s, language)}" for i, s in enumerate(slots)]
    return "\n".join(lines)


# ── Natural language datetime parsing ─────────────────────────────────────────

def parse_datetime_from_text(text: str, clinic: Clinic) -> tuple[Optional[datetime], Optional[str]]:
    """
    Parse a natural language datetime expression into a datetime + time preference.
    Returns (date, time_preference) or (None, None) if unparseable.

    Handles:
      - "tomorrow morning"
      - "Friday afternoon"
      - "kesho asubuhi"
      - "next Monday"
      - Specific times: "Friday at 3pm"
    """
    tz   = pytz.timezone(TIMEZONE)
    now  = datetime.now(tz)
    text = text.lower().strip()

    time_pref = None

    # Time of day preference
    if any(w in text for w in ["morning", "asubuhi"]):
        time_pref = "morning"
    elif any(w in text for w in ["afternoon", "mchana", "alasiri"]):
        time_pref = "afternoon"
    elif any(w in text for w in ["evening", "jioni"]):
        time_pref = "evening"

    # Relative day expressions
    if any(w in text for w in ["today", "leo"]):
        return now, time_pref

    if any(w in text for w in ["tomorrow", "kesho"]):
        return now + timedelta(days=1), time_pref

    # Day names (English + Swahili)
    day_map = {
        "monday": 0, "jumatatu": 0,
        "tuesday": 1, "jumanne": 1,
        "wednesday": 2, "jumatano": 2,
        "thursday": 3, "alhamisi": 3,
        "friday": 4, "ijumaa": 4,
        "saturday": 5, "jumamosi": 5,
        "sunday": 6, "jumapili": 6,
    }

    for day_name, weekday in day_map.items():
        if day_name in text:
            days_ahead = (weekday - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7   # "Friday" means next Friday if today is Friday
            return now + timedelta(days=days_ahead), time_pref

    # Specific time parsing: "at 3pm", "at 10:30"
    time_match = re.search(r"at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if time_match:
        hour   = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        period = time_match.group(3)
        if period == "pm" and hour < 12:
            hour += 12
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)
        return target, None

    return None, None
