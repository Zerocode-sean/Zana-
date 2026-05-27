from tools.language_tool import detect_language, normalize_language
from models.schemas import Language


class TestDetectLanguage:
    def test_english_detected(self):
        assert detect_language("Hello, how are you?") == Language.ENGLISH

    def test_english_with_generic_text(self):
        assert detect_language("I would like to book an appointment") == Language.ENGLISH

    def test_swahili_detected(self):
        assert detect_language("Nataka kupanga miadi") == Language.SWAHILI

    def test_swahili_single_word(self):
        assert detect_language("habari") == Language.SWAHILI

    def test_sheng_detected(self):
        assert detect_language("Mambo vipi buda") == Language.SHENG

    def test_sheng_short_phrase(self):
        assert detect_language("poa sana") == Language.SHENG

    def test_sheng_takes_priority_over_swahili(self):
        """Sheng detection should take priority when both Sheng and Swahili keywords present."""
        assert detect_language("Mambo habari") == Language.SHENG

    def test_mixed_language_favors_swahili(self):
        assert detect_language("Sawa, I will come tomorrow asubuhi") == Language.SWAHILI

    def test_empty_string(self):
        assert detect_language("") == Language.ENGLISH

    def test_numbers_only(self):
        assert detect_language("123") == Language.ENGLISH

    def test_case_insensitive(self):
        assert detect_language("HABARI") == Language.SWAHILI
        assert detect_language("MAMBO") == Language.SHENG


class TestNormalizeLanguage:
    def test_english(self):
        assert normalize_language(Language.ENGLISH) == "EN"

    def test_swahili(self):
        assert normalize_language(Language.SWAHILI) == "SW"

    def test_sheng_falls_back_to_swahili(self):
        assert normalize_language(Language.SHENG) == "SW"


class TestDynamicLanguageSwitching:
    """Verify each message's language is detected independently."""

    def test_swahili_then_english(self):
        first = detect_language("Habari, nataka kupanga miadi")
        second = detect_language("What are your opening hours")
        assert first == Language.SWAHILI
        assert second == Language.ENGLISH

    def test_english_then_swahili(self):
        first = detect_language("Hello, I want to book")
        second = detect_language("Leo kesho asubuhi")
        assert first == Language.ENGLISH
        assert second == Language.SWAHILI

    def test_mixed_language_detection(self):
        msg = "Sawa, I will come tomorrow asubuhi"
        assert detect_language(msg) in (Language.SWAHILI, Language.SHENG)
