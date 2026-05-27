from models.schemas import Language

# ── Keyword signals per language ──────────────────────────────────────────────
SWAHILI_SIGNALS = {
    "habari", "nataka", "miadi", "sawa", "tafadhali", "karibu", "asante",
    "daktari", "sijui", "nitakuja", "nakuja", "kliniki", "leo", "kesho",
    "asubuhi", "jioni", "usiku", "mchana", "nzuri", "pamoja", "ninahitaji",
    "naweza", "unaweza", "swali", "jibu", "futa", "badilisha", "kubali",
    "saa", "dakika", "wiki", "mwezi", "tarehe", "jina", "dawa", "mgonjwa",
}

SHENG_SIGNALS = {
    "mambo", "poa", "si mbaya", "sawa tu", "nipigie", "nisaidie", "uko",
    "niko", "unataka", "ninataka", "vipi", "buda", "msee", "dem", "kama",
    "ama", "kweli", "fiti", "safi", "inabidi", "lazima", "shida", "ngori",
}


def detect_language(text: str) -> Language:
    """
    Detect the dominant language from a message.
    Returns Language enum: EN, SW, or SHENG.

    Strategy:
    1. Check for Sheng first (most specific)
    2. Check for Swahili keywords
    3. Default to English
    """
    lower = text.lower()
    words = set(lower.split())

    sheng_hits   = words & SHENG_SIGNALS
    swahili_hits = words & SWAHILI_SIGNALS

    if sheng_hits:
        return Language.SHENG
    if swahili_hits:
        return Language.SWAHILI

    # Also check for multi-word Sheng phrases
    for phrase in ["si mbaya", "sawa tu", "mambo vipi", "poa sana"]:
        if phrase in lower:
            return Language.SHENG

    return Language.ENGLISH


def normalize_language(language: Language) -> str:
    """
    Map Language enum to the 2-letter suffix used in MESSAGES dict.
    SHENG falls back to Swahili for message templates.
    """
    return {
        Language.ENGLISH: "EN",
        Language.SWAHILI: "SW",
        Language.SHENG:   "SW",   # Sheng patients get Swahili templates
    }[language]
