"""
Скоринг вакансии 0–10.
- hard_prefilter() — дешёвый, бесплатный отсев ДО обращения к Gemini
  (стоп-слова, стоп-роли, антиспам, жёсткий remote-фильтр с исключением
  "гибрид, но Сербия").
- score_vacancy() — полный rule-based скоринг, запасной вариант, если
  Gemini недоступен (нет ключа, кончился лимит, сбой сети).
"""
import re
from extract import detect_format, detect_location


def _stem_pattern(phrase: str) -> re.Pattern:
    words = phrase.split()
    parts = []
    for w in words:
        if len(w) > 5 and re.match(r"^[а-яё]+$", w, re.IGNORECASE):
            stem = w[:-2]
        else:
            stem = w
        parts.append(re.escape(stem) + r"\w*")
    pattern = r"\s+".join(parts)
    return re.compile(pattern, re.IGNORECASE)


def _contains_any(text: str, phrases: list[str]) -> bool:
    for phrase in phrases:
        if " " in phrase and re.match(r"^[а-яёА-ЯЁ\s\-]+$", phrase):
            if _stem_pattern(phrase).search(text):
                return True
        elif phrase.lower() in text.lower():
            return True
    return False


def hard_prefilter(vac: dict, criteria: dict) -> tuple[bool, str]:
    """Бесплатный, быстрый отсев ДО обращения к ИИ.
    "Формат не указан" НЕ отсекается — многие посты в удалённых каналах не
    повторяют слово remote в каждом объявлении, это не доказательство офиса.
    Исключение по гибриду: если формат "Гибрид", но в тексте явно упомянута
    Сербия — пропускаем (единственная локация, где гибрид рассматривается)."""
    text = vac.get("raw_text", "") or (vac.get("title", "") + " " + vac.get("snippet", ""))

    if _contains_any(text, criteria["stop_words"]):
        return False, "стоп-слово (индустрия/тип роли не подходит)"
    if _contains_any(vac.get("title", ""), criteria["stop_roles"]):
        return False, "стоп-роль (не операционное направление)"
    if _contains_any(text, criteria.get("ad_post_stop_phrases", [])):
        return False, "похоже на рекламный пост (вебинар/курс/мероприятие), не вакансия"

    schedule = (vac.get("schedule") or "").lower()
    fmt = "Удалённо" if schedule in criteria.get("remote_schedule_values", []) else detect_format(text)
    location = detect_location(text)

    if fmt == "Офис":
        return False, "формат не подходит: офис, нужен строго remote"
    if fmt == "Гибрид":
        if location != "Сербия":
            return False, "формат не подходит: гибрид (не Сербия), нужен строго remote"
        # гибрид + Сербия — осознанное исключение, пропускаем дальше

    return True, ""


def score_vacancy(vac: dict, criteria: dict) -> tuple[int, list[str]]:
    """Rule-based скоринг — запасной вариант, если Gemini недоступен."""
    text = vac.get("raw_text", "") or (vac.get("title", "") + " " + vac.get("snippet", ""))
    reasons = []
    score = 0

    passed, reject_reason = hard_prefilter(vac, criteria)
    if not passed:
        return 0, [reject_reason]

    schedule = (vac.get("schedule") or "").lower()
    fmt = "Удалённо" if schedule in criteria.get("remote_schedule_values", []) else detect_format(text)
    location = detect_location(text)

    if fmt == "Удалённо":
        score += 2
        reasons.append("подтверждённо удалённо")
    elif fmt == "Гибрид" and location == "Сербия":
        score += 1
        reasons.append("гибрид в Сербии — рассматриваем как исключение")

    if _contains_any(text, criteria["roles_keywords"]):
        score += 4
        reasons.append("совпадение по роли")
    elif _contains_any(text, criteria.get("watchlist_keywords", [])):
        score += 2
        reasons.append("роль из watchlist (Chief of Staff и т.п.)")

    if _contains_any(text, criteria["part_time_hints"]):
        score += 1
        reasons.append("part-time / проектная занятость")

    if _contains_any(text, criteria["priority_industry_keywords"]):
        score += 2
        reasons.append("приоритетная индустрия (health/edtech/психология/НКО)")

    if _contains_any(text, criteria.get("target_companies", [])):
        score += 2
        reasons.append("компания из списка HyperCareer (рус. корни, зарубежный рынок)")

    salary_text = vac.get("salary_text", "") or ""
    numbers = [int(n) for n in re.findall(r"\d{5,7}", salary_text.replace(" ", ""))]
    if numbers:
        max_salary = max(numbers)
        if max_salary >= criteria["salary_min_full_time_equivalent_rub"]:
            score += 1
            reasons.append(f"зарплата от {max_salary:,} ₽".replace(",", " "))
    else:
        reasons.append("зарплата не указана")

    return min(score, 10), reasons
