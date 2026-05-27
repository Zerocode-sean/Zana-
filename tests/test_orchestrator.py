"""Tests for the orchestrator's intent detection fallback and state logic."""

from agents.orchestrator import _fallback_intent
from models.schemas import Intent


class TestFallbackIntent:
    def test_urgent_medical_chest_pain(self):
        assert _fallback_intent("I have chest pain") == Intent.URGENT_MEDICAL

    def test_urgent_medical_emergency(self):
        assert _fallback_intent("This is an emergency") == Intent.URGENT_MEDICAL

    def test_urgent_medical_shortness_of_breath(self):
        assert _fallback_intent("I can't breathe") == Intent.URGENT_MEDICAL

    def test_urgent_medical_seizure(self):
        assert _fallback_intent("My child is having a seizure") == Intent.URGENT_MEDICAL

    def test_book_appointment_keyword(self):
        assert _fallback_intent("I want to book an appointment") == Intent.BOOK_APPOINTMENT

    def test_book_appointment_schedule(self):
        assert _fallback_intent("Schedule a visit") == Intent.BOOK_APPOINTMENT

    def test_book_appointment_swahili(self):
        assert _fallback_intent("Nataka kupanga miadi") == Intent.BOOK_APPOINTMENT

    def test_confirm_appointment_yes(self):
        assert _fallback_intent("yes") == Intent.CONFIRM_APPOINTMENT

    def test_confirm_appointment_ndiyo(self):
        assert _fallback_intent("ndiyo") == Intent.CONFIRM_APPOINTMENT

    def test_confirm_appointment_numeric(self):
        assert _fallback_intent("1") == Intent.CONFIRM_APPOINTMENT

    def test_cancel_appointment_no(self):
        assert _fallback_intent("no") == Intent.CANCEL_APPOINTMENT

    def test_cancel_appointment_sitakuja(self):
        assert _fallback_intent("sitakuja") == Intent.CANCEL_APPOINTMENT

    def test_cancel_appointment_numeric(self):
        assert _fallback_intent("2") == Intent.CANCEL_APPOINTMENT

    def test_reschedule_keyword(self):
        assert _fallback_intent("I need to reschedule") == Intent.RESCHEDULE

    def test_reschedule_swahili(self):
        assert _fallback_intent("Nataka kubadilisha") == Intent.RESCHEDULE

    def test_greeting_hello(self):
        assert _fallback_intent("hello") == Intent.GREETING

    def test_greeting_habari(self):
        assert _fallback_intent("habari") == Intent.GREETING

    def test_greeting_mambo(self):
        assert _fallback_intent("mambo") == Intent.GREETING

    def test_general_query_hours(self):
        assert _fallback_intent("What are your hours") == Intent.GENERAL_QUERY

    def test_general_query_location_swahili(self):
        assert _fallback_intent("wapi kliniki") == Intent.GENERAL_QUERY

    def test_general_query_price(self):
        assert _fallback_intent("How much does it cost") == Intent.GENERAL_QUERY

    def test_general_query_charge(self):
        assert _fallback_intent("how much do you charge") == Intent.GENERAL_QUERY

    def test_general_query_pricing(self):
        assert _fallback_intent("What is your pricing") == Intent.GENERAL_QUERY

    def test_general_query_remind(self):
        assert _fallback_intent("how do you remind me") == Intent.GENERAL_QUERY

    def test_general_query_question(self):
        assert _fallback_intent("i have questions") == Intent.GENERAL_QUERY

    def test_unknown_unrecognized(self):
        assert _fallback_intent("The sky is purple today") == Intent.UNKNOWN

    def test_unknown_empty(self):
        assert _fallback_intent("") == Intent.UNKNOWN

    def test_keyword_priority_order(self):
        """URGENT_MEDICAL keywords should take priority."""
        assert _fallback_intent("hello, I have chest pain") == Intent.URGENT_MEDICAL

    # Word-boundary tests — short tokens must not match inside other words
    def test_yes_within_other_words_not_confirmation(self):
        """'yes which slots are available' should be BOOK_APPOINTMENT (slot keyword)."""
        assert _fallback_intent("yes which slots are available") == Intent.BOOK_APPOINTMENT

    def test_standalone_yes_is_confirmation(self):
        assert _fallback_intent("yes") == Intent.CONFIRM_APPOINTMENT

    def test_no_within_other_words_not_cancel(self):
        """'no' in 'notebook' should NOT match CANCEL."""
        result = _fallback_intent("notebook")
        assert result != Intent.CANCEL_APPOINTMENT

    def test_standalone_no_is_cancel(self):
        assert _fallback_intent("no") == Intent.CANCEL_APPOINTMENT

    # Slot keyword → BOOK_APPOINTMENT
    def test_slot_keyword_triggers_booking(self):
        assert _fallback_intent("which slots are available") == Intent.BOOK_APPOINTMENT

    def test_available_slots_triggers_booking(self):
        assert _fallback_intent("Do you have any slots today") == Intent.BOOK_APPOINTMENT

    # Multi-word greeting still works
    def test_good_morning_greeting(self):
        assert _fallback_intent("good morning") == Intent.GREETING

    def test_good_evening_greeting(self):
        assert _fallback_intent("good evening") == Intent.GREETING

    def test_hello_how_are_you_is_greeting(self):
        """'hello' as a standalone word should be greeting."""
        assert _fallback_intent("hello, how are you") == Intent.GREETING
