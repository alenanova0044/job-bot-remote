"""
Скоринг вакансии 0–10 по критериям из criteria.json.
Правило-based, без внешних ИИ-API — бесплатно, предсказуемо, без лимитов.
Логику легко объяснить и подкрутить руками, когда увидишь, что фильтр где-то ошибается.
"""
import re


def _contains_any(text: str, words: list[str]) -> bool:
    text_low = text.lower()
    return any(w.lower() in text_low for w in words)


def score_vacancy(vac: dict, criteria: dict) -> tuple[int, list[str]]:
    """Возвращает (score, причины) — причины нужны, чтобы в сообщении в Telegram
    было видно, ПОЧЕМУ бот посчитал вакансию релевантной."""
    text = vac.get("raw_text", "") or (vac.get("title", "") + " " + vac.get("snippet", ""))
    reasons = []
    score = 0

    # Стоп-факторы — сразу на выход
    if _contains_any(text, criteria["stop_words"]):
        return 0, ["стоп-слово (индустрия/тип роли не подходит)"]
    if _contains_any(vac.get("title", ""), criteria["stop_roles"]):
        return 0, ["стоп-роль (не операционное направление)"]
    if _contains_any(text, criteria.get("ad_post_stop_phrases", [])):
        return 0, ["похоже на рекламный пост (вебинар/курс/мероприятие), не вакансия"]

    # Роль
    if _contains_any(text, criteria["roles_keywords"]):
        score += 4
        reasons.append("совпадение по роли")
    elif _contains_any(text, criteria.get("watchlist_keywords", [])):
        score += 2
        reasons.append("роль из watchlist (Chief of Staff и т.п.)")

    # Формат / частичная занятость
    schedule = (vac.get("schedule") or "").lower()
    if schedule in criteria.get("remote_schedule_values", []) or _contains_any(text, criteria["part_time_hints"]):
        score += 2
        reasons.append("удалённо / частичная занятость")

    # Приоритетные индустрии
    if _contains_any(text, criteria["priority_industry_keywords"]):
        score += 2
        reasons.append("приоритетная индустрия (health/edtech/психология/НКО)")

    # Зарплата
    salary_text = vac.get("salary_text", "") or ""
    numbers = [int(n) for n in re.findall(r"\d{5,7}", salary_text.replace(" ", ""))]
    if numbers:
        max_salary = max(numbers)
        if max_salary >= criteria["salary_min_full_time_equivalent_rub"]:
            score += 2
            reasons.append(f"зарплата от {max_salary:,} ₽".replace(",", " "))
    else:
        score += 1  # зарплата не указана — не штрафуем, но и не поощряем сильно
        reasons.append("зарплата не указана")

    return min(score, 10), reasons
