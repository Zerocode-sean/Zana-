from datetime import datetime, timezone
from models.schemas import Clinic, WorkingHours, BreakTime, Language
from tools.availability_tool import (
    generate_slots,
    format_slot,
    format_slots_list,
    parse_datetime_from_text,
)


def _make_clinic(**overrides) -> Clinic:
    defaults = dict(
        clinic_id="test_clinic",
        name="Test Clinic",
        doctors=["Dr. Test"],
        services=["General Consultation"],
        working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        working_hours=WorkingHours(start="08:00", end="17:00"),
        break_time=BreakTime(start="13:00", end="14:00"),
        slot_duration=30,
        whatsapp_number="+254700000000",
        owner_phone="+254711111111",
        language_preference=Language.ENGLISH,
        location="Nairobi",
    )
    defaults.update(overrides)
    return Clinic(**defaults)


class TestGenerateSlots:
    def test_working_day_returns_slots(self):
        clinic = _make_clinic(slot_duration=30)
        date = datetime(2026, 5, 18)  # Monday
        slots = generate_slots(clinic, date)
        # 08:00 to 17:00 = 9h, minus 1h break = 8h = 16 slots at 30min
        assert len(slots) == 16
        assert slots[0].hour == 8 and slots[0].minute == 0
        assert slots[-1].hour == 16 and slots[-1].minute == 30

    def test_non_working_day_returns_empty(self):
        clinic = _make_clinic(working_days=["Monday", "Tuesday"])
        date = datetime(2026, 5, 16)  # Saturday
        assert generate_slots(clinic, date) == []

    def test_respects_break_time(self):
        clinic = _make_clinic(
            working_hours=WorkingHours(start="08:00", end="17:00"),
            break_time=BreakTime(start="13:00", end="14:00"),
            slot_duration=30,
        )
        date = datetime(2026, 5, 19)  # Tuesday
        slots = generate_slots(clinic, date)
        # No slots between 13:00 and 14:00
        for s in slots:
            assert s.hour != 13
        # Slot at 12:30 should exist
        assert any(s.hour == 12 and s.minute == 30 for s in slots)
        # Slot at 14:00 should exist (after break)
        assert any(s.hour == 14 and s.minute == 0 for s in slots)

    def test_short_slot_duration(self):
        clinic = _make_clinic(slot_duration=15)
        date = datetime(2026, 5, 20)  # Wednesday
        slots = generate_slots(clinic, date)
        # 08:00 to 17:00 = 9h, minus 1h break = 8h = 32 slots at 15min
        assert len(slots) == 32
        assert slots[0].minute == 0
        assert slots[1].minute == 15


class TestFormatSlot:
    def test_basic_format(self):
        dt = datetime(2026, 5, 18, 10, 0)
        result = format_slot(dt)
        assert "Monday" in result
        assert "18" in result
        assert "May" in result
        assert "10:00" in result or "10:00 AM" in result

    def test_afternoon_time(self):
        dt = datetime(2026, 5, 18, 14, 30)
        result = format_slot(dt)
        assert "02:30" in result or "2:30" in result
        assert "PM" in result or "pm" in result


class TestFormatSlotsList:
    def test_single_slot(self):
        slots = [datetime(2026, 5, 18, 9, 0)]
        result = format_slots_list(slots)
        assert "1" in result

    def test_multiple_slots(self):
        slots = [
            datetime(2026, 5, 18, 9, 0),
            datetime(2026, 5, 18, 10, 0),
        ]
        result = format_slots_list(slots)
        assert "1" in result
        assert "2" in result


class TestParseDatetimeFromText:
    def test_tomorrow_morning(self, monkeypatch):
        from tools import availability_tool as at

        fake_now = datetime(2026, 5, 18, 8, 0)
        monkeypatch.setattr(
            at,
            "datetime",
            type(
                "FakeDatetime",
                (),
                {
                    "now": classmethod(lambda cls, tz: fake_now),
                    "__getattr__": lambda self, name: getattr(datetime, name),
                },
            ),
        )
        clinic = _make_clinic()
        date, pref = parse_datetime_from_text("tomorrow morning", clinic)
        assert date is not None
        assert date.day == 19
        assert pref == "morning"

    def test_specific_day(self, monkeypatch):
        from tools import availability_tool as at

        fake_now = datetime(2026, 5, 18, 8, 0)  # Monday
        monkeypatch.setattr(
            at,
            "datetime",
            type(
                "FakeDatetime",
                (),
                {
                    "now": classmethod(lambda cls, tz: fake_now),
                    "__getattr__": lambda self, name: getattr(datetime, name),
                },
            ),
        )
        clinic = _make_clinic()
        date, pref = parse_datetime_from_text("Friday afternoon", clinic)
        assert date is not None
        assert date.weekday() == 4  # Friday
        assert pref == "afternoon"

    def test_specific_time(self, monkeypatch):
        from tools import availability_tool as at

        fake_now = datetime(2026, 5, 18, 8, 0)
        monkeypatch.setattr(
            at,
            "datetime",
            type(
                "FakeDatetime",
                (),
                {
                    "now": classmethod(lambda cls, tz: fake_now),
                    "__getattr__": lambda self, name: getattr(datetime, name),
                },
            ),
        )
        clinic = _make_clinic()
        date, pref = parse_datetime_from_text("at 3pm", clinic)
        assert date is not None
        assert date.hour == 15
        assert pref is None

    def test_swahili_tomorrow(self, monkeypatch):
        from tools import availability_tool as at

        fake_now = datetime(2026, 5, 18, 8, 0)
        monkeypatch.setattr(
            at,
            "datetime",
            type(
                "FakeDatetime",
                (),
                {
                    "now": classmethod(lambda cls, tz: fake_now),
                    "__getattr__": lambda self, name: getattr(datetime, name),
                },
            ),
        )
        clinic = _make_clinic()
        date, pref = parse_datetime_from_text("kesho asubuhi", clinic)
        assert date is not None
        assert date.day == 19
        assert pref == "morning"

    def test_unparseable_returns_none(self, monkeypatch):
        from tools import availability_tool as at

        fake_now = datetime(2026, 5, 18, 8, 0)
        monkeypatch.setattr(
            at,
            "datetime",
            type(
                "FakeDatetime",
                (),
                {
                    "now": classmethod(lambda cls, tz: fake_now),
                    "__getattr__": lambda self, name: getattr(datetime, name),
                },
            ),
        )
        clinic = _make_clinic()
        date, pref = parse_datetime_from_text("blah blah blah", clinic)
        assert date is None
        assert pref is None
