"""
Простое, без ИИ, извлечение формата работы и локации из сырого текста вакансии.
Используется как запасной вариант, когда Gemini недоступен, и как источник
"схемы" (schedule) для дешёвого hard_prefilter в scorer.py.
"""
import re

REMOTE_HINTS = [
    "remote", "full remote", "fully remote", "work from anywhere", "anywhere",
    "удал", "полностью удал", "из любой точки", "дистанцион",
]
HYBRID_HINTS = ["гибрид", "hybrid"]
ONSITE_HINTS = [
    "офис", "on-site", "onsite", "in office", "in-office",
    "приезжать в офис", "работа в офисе", "только в офисе",
]

COUNTRY_HINTS = [
    ("worldwide", "по всему миру"), ("любая страна", "по всему миру"),
    ("весь мир", "по всему миру"), ("any location", "по всему миру"),
    ("россия", "Россия"), ("russia", "Россия"),
    ("сербия", "Сербия"), ("serbia", "Сербия"),
    ("кипр", "Кипр"), ("cyprus", "Кипр"),
    ("грузия", "Грузия"), ("georgia", "Грузия"),
    ("армения", "Армения"), ("armenia", "Армения"),
    ("казахстан", "Казахстан"), ("kazakhstan", "Казахстан"),
    ("турция", "Турция"), ("turkey", "Турция"),
    ("оаэ", "ОАЭ"), ("uae", "ОАЭ"), ("dubai", "ОАЭ"), ("дубай", "ОАЭ"),
    ("европа", "Европа"), ("europe", "Европа"), (" eu ", "Европа"),
    ("сша", "США"), ("usa", "США"), (" us ", "США"),
    ("великобритания", "Великобритания"), ("uk ", "Великобритания"),
    ("германия", "Германия"), ("germany", "Германия"),
    ("португалия", "Португалия"), ("portugal", "Португалия"),
    ("испания", "Испания"), ("spain", "Испания"),
    ("польша", "Польша"), ("poland", "Польша"),
    ("снг", "СНГ"),
]


def detect_format(text: str) -> str:
    t = (text or "").lower()
    if any(h in t for h in HYBRID_HINTS):
        return "Гибрид"
    if any(h in t for h in ONSITE_HINTS) and not any(h in t for h in REMOTE_HINTS):
        return "Офис"
    if any(h in t for h in REMOTE_HINTS):
        return "Удалённо"
    return "Не указан"


def detect_location(text: str) -> str:
    t = (text or "").lower()
    for hint, label in COUNTRY_HINTS:
        if hint in t:
            return label
    return "не указана"


def short_description(text: str, max_len: int = 220) -> str:
    clean = re.sub(r"\s+", " ", (text or "")).strip()
    if len(clean) <= max_len:
        return clean
    return clean[:max_len].rsplit(" ", 1)[0] + "…"


def detect_target_company(text: str, target_companies: list[str]) -> str | None:
    """Возвращает название компании из списка HyperCareer, если оно упомянуто в тексте."""
    t = (text or "").lower()
    for name in target_companies:
        if name.lower() in t:
            return name
    return None
