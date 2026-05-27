"""
Zana — Clinic Onboarding Script
─────────────────────────────────
Run this once to register a new clinic in Firestore.
In Phase 2 this becomes a WhatsApp-based onboarding flow.

Usage:
  python -m scripts.seed_clinic
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.firestore_client import get_db
from models.schemas import Clinic, WorkingHours, BreakTime, Language


def seed_clinic():
    """Register a demo clinic — edit this to match the real clinic."""

    clinic = Clinic(
        clinic_id="riverside_medical_001",
        name="Riverside Medical Clinic",
        doctors=["Dr. Kamau", "Dr. Achieng"],
        services=[
            "General Consultation",
            "Dental",
            "Physiotherapy",
            "Maternal Health",
            "Child Wellness",
        ],
        working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        working_hours=WorkingHours(start="08:00", end="17:00"),
        break_time=BreakTime(start="13:00", end="14:00"),
        slot_duration=30,  # 30-minute appointments
        whatsapp_number="+254758152033",  # The clinic's WhatsApp number
        owner_phone="+254711111111",  # Dr. Kamau's personal number for alerts
        language_preference=Language.ENGLISH,
        location="Riverside Drive, Nairobi. Next to the Shell petrol station.",
    )

    db = get_db()
    ref = db.collection("clinics").document(clinic.clinic_id)
    ref.set(clinic.model_dump())

    print(f"✅ Clinic registered: {clinic.name}")
    print(f"   ID:        {clinic.clinic_id}")
    print(f"   WhatsApp:  {clinic.whatsapp_number}")
    print(f"   Owner:     {clinic.owner_phone}")
    print(f"   Doctors:   {', '.join(clinic.doctors)}")
    print(f"   Services:  {', '.join(clinic.services)}")
    print(f"\n🚀 Zana is ready to serve {clinic.name} patients.")


if __name__ == "__main__":
    seed_clinic()
