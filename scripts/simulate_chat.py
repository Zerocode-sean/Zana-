"""Interactive local chat simulator for the Zana orchestrator.

This runs the message pipeline without Firestore or WhatsApp so you can
try a conversation like a real user would.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from agents import orchestrator as orch
from models.schemas import (
    AppointmentStatus,
    BreakTime,
    Clinic,
    ConversationState,
    IncomingMessage,
    Language,
    Patient,
    WorkingHours,
)


@dataclass
class MemoryStore:
    patient: Patient
    clinic: Clinic
    conversation_context: dict[str, Any] = field(default_factory=dict)
    sent_messages: list[tuple[str, str]] = field(default_factory=list)
    appointments: list[dict[str, Any]] = field(default_factory=list)


class FakeDateTime:
    @staticmethod
    def fromisoformat(value: str):
        return datetime.fromisoformat(value)


async def run_chat(messages: list[str], store: MemoryStore | None = None) -> MemoryStore:
    if store is None:
        clinic = Clinic(
            clinic_id="riverside_medical_001",
            name="Riverside Medical Clinic",
            doctors=["Dr. Kamau"],
            services=["General Consultation", "Dental", "Physiotherapy"],
            working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            working_hours=WorkingHours(start="08:00", end="17:00"),
            break_time=BreakTime(start="13:00", end="14:00"),
            slot_duration=30,
            whatsapp_number="+254700000000",
            owner_phone="+254711111111",
            language_preference=Language.ENGLISH,
            location="Nairobi",
        )
        store = MemoryStore(
            patient=Patient(phone="+254712345678", clinic_id=clinic.clinic_id),
            clinic=clinic,
        )
    else:
        clinic = store.clinic

    async def fake_send_message(to: str, body: str) -> dict:
        store.sent_messages.append((to, body))
        print(f"Zana -> {to}: {body}")
        return {"status": "ok"}

    def fake_get_or_create_patient(phone: str, clinic_id: str) -> Patient:
        return store.patient

    def fake_get_clinic(clinic_id: str) -> Clinic:
        return store.clinic

    def fake_update_patient(phone: str, updates: dict) -> None:
        for key, value in updates.items():
            if key == "conversation_state":
                store.patient.conversation_state = ConversationState(value)
            elif key == "conversation_context":
                store.conversation_context = value
                store.patient.conversation_context = value
            elif key == "language":
                store.patient.language = Language(value)
            elif key == "name":
                store.patient.name = value
            elif key == "unknown_intent_count":
                store.patient.unknown_intent_count = value
            else:
                setattr(store.patient, key, value)

    def fake_set_conversation_state(
        phone: str, state: ConversationState, context: dict | None = None
    ) -> None:
        store.patient.conversation_state = state
        if context is not None:
            store.conversation_context = context
            store.patient.conversation_context = context

    def fake_get_conversation_context(phone: str) -> dict:
        return store.conversation_context

    def fake_increment_unknown_intent(phone: str) -> int:
        store.patient.unknown_intent_count += 1
        return store.patient.unknown_intent_count

    def fake_reset_unknown_intent(phone: str) -> None:
        store.patient.unknown_intent_count = 0

    def fake_set_patient_language(phone: str, language: Language) -> None:
        store.patient.language = language

    def fake_create_appointment(
        clinic_id: str,
        patient_phone: str,
        patient_name: str,
        doctor_name: str,
        service: str,
        dt: datetime,
    ) -> None:
        store.appointments.append(
            {
                "clinic_id": clinic_id,
                "patient_phone": patient_phone,
                "patient_name": patient_name,
                "doctor_name": doctor_name,
                "service": service,
                "datetime_utc": dt,
                "status": AppointmentStatus.BOOKED.value,
            }
        )

    def fake_cancel_appointment(clinic_id: str, appointment_id: str) -> None:
        return None

    def fake_confirm_appointment(clinic_id: str, appointment_id: str) -> None:
        return None

    def fake_get_available_slots(*args, **kwargs):
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        return [now + timedelta(days=1, hours=2), now + timedelta(days=1, hours=3)]

    def fake_parse_datetime_from_text(text: str, clinic: Clinic):
        return datetime.now(timezone.utc) + timedelta(days=1), "morning"

    def fake_format_slots_list(slots, lang):
        return "\n".join(
            f"{idx + 1}. {slot.strftime('%Y-%m-%d %H:%M')}" for idx, slot in enumerate(slots)
        )

    async def fake_generate_reply(
        patient_message: str, clinic: Clinic, lang: str, patient_name: str | None = None
    ) -> str | None:
        return None  # fall back to template

    orch.send_message = fake_send_message
    orch.get_or_create_patient = fake_get_or_create_patient
    orch.get_clinic = fake_get_clinic
    orch.update_patient = fake_update_patient
    orch.set_conversation_state = fake_set_conversation_state
    orch.get_conversation_context = fake_get_conversation_context
    orch.increment_unknown_intent = fake_increment_unknown_intent
    orch.reset_unknown_intent = fake_reset_unknown_intent
    orch.set_patient_language = fake_set_patient_language
    orch.create_appointment = fake_create_appointment
    orch.cancel_appointment = fake_cancel_appointment
    orch.confirm_appointment = fake_confirm_appointment
    orch.get_available_slots = fake_get_available_slots
    orch.parse_datetime_from_text = fake_parse_datetime_from_text
    orch.format_slots_list = fake_format_slots_list
    orch.datetime = FakeDateTime
    orch._generate_reply = fake_generate_reply

    for message in messages:
        print(f"You -> {message}")
        incoming = IncomingMessage(
            from_phone=store.patient.phone,
            message_body=message,
            message_id=f"local-{len(store.sent_messages) + 1}",
            timestamp=datetime.now(timezone.utc),
            clinic_id=store.clinic.clinic_id,
        )
        await orch.handle_message(incoming)
        print()

    return store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Zana chat simulation.")
    parser.add_argument(
        "messages",
        nargs="*",
        help="Messages to send in sequence. If omitted, an interactive prompt opens.",
    )
    return parser.parse_args()


async def interactive_chat(store: MemoryStore | None = None) -> None:
    if store is None:
        store = await run_chat([])

    print("\nType messages like a patient. Press Enter on an empty line to quit.\n")
    while True:
        try:
            message = input("You -> ").strip()
        except EOFError:
            break
        if not message:
            break
        store = await run_chat([message], store=store)


async def main() -> None:
    args = parse_args()
    store = None
    if args.messages:
        store = await run_chat(args.messages)
        print("\n✨ Continue chatting below (or press Ctrl+C to quit):")
    await interactive_chat(store=store)


if __name__ == "__main__":
    asyncio.run(main())
