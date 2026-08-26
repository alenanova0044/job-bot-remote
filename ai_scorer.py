"""
Финальный скоринг вакансии через Gemini (бесплатный тир Google AI Studio).
Вызывается ТОЛЬКО для вакансий, прошедших дешёвый hard_prefilter() — так экономим
лимит бесплатных запросов. Если ключа нет или Gemini недоступен — вызывающий код
(bot.py) сам откатывается на rule-based score_vacancy() из scorer.py.
"""
import json
import os
import re
import requests

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def _build_prompt(vac: dict, criteria: dict) -> str:
    roles = ", ".join(criteria["roles_keywords"][:12])
    industries = ", ".join(criteria["priority_industry_keywords"][:15])
    companies = ", ".join(criteria.get("target_companies", [])[:30])
    stop_industries = ", ".join(criteria["stop_words"][:10])

    return f"""Ты — рекрутер-ассистент. Оцени, насколько вакансия подходит кандидату.

ПРОФИЛЬ КАНДИДАТА:
- Целевые роли: {roles} (и близкие по смыслу формулировки, не только точные совпадения)
- Приоритетные индустрии (бонус, не обязательное условие): {industries}
- Компании с российскими корнями, работающие на зарубежном рынке (плюс, если совпадёт): {companies}
- Индустрии, которые НЕ интересны: {stop_industries}
- Формат работы: строго удалённо (remote). Гибрид допустим ТОЛЬКО если локация — Сербия. Офис не подходит никогда.
- Занятость: part-time/проектная в приоритете, но full-time тоже рассматривается
- Целевая зарплата (full-time эквивалент): от {criteria['salary_min_full_time_equivalent_rub']} ₽/мес, если указана

ТЕКСТ ВАКАНСИИ:
{vac.get('raw_text', '')[:1500]}

Ответь СТРОГО в формате JSON, без markdown-разметки, без пояснений вне JSON:
{{
  "score": <целое число 0-10, где 10 — идеальное совпадение>,
  "reason": "<1-2 предложения на русском, почему кандидату стоит или не стоит откликаться>",
  "format": "<Удалённо / Гибрид / Офис / Не указан>",
  "location": "<страна/регион, если указаны в тексте, иначе 'не указана'>"
}}

Если формат работы явно НЕ remote (офис, или гибрид не в Сербии) — ставь score строго 0."""


def ai_score_vacancy(vac: dict, criteria: dict) -> dict | None:
    """Возвращает {"score":.., "reason":.., "format":.., "location":..} или None при любой ошибке —
    вызывающий код должен в этом случае откатиться на rule-based score_vacancy()."""
    if not GEMINI_API_KEY:
        return None

    prompt = _build_prompt(vac, criteria)
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        parsed = json.loads(raw)

        score = int(parsed.get("score", 0))
        return {
            "score": max(0, min(score, 10)),
            "reason": str(parsed.get("reason", "")).strip(),
            "format": str(parsed.get("format", "Не указан")).strip(),
            "location": str(parsed.get("location", "не указана")).strip(),
        }
    except Exception as e:
        print(f"[ai_scorer] Ошибка вызова Gemini: {e}")
        return None
