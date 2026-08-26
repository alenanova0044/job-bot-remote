"""
Главный скрипт — запускается по расписанию (см. README).
Один проход: собрать вакансии → дешёвый rule-based отсев → финальная оценка
через Gemini (с откатом на rule-based, если ИИ недоступен) → отправить новые
подходящие в Telegram-группу → сохранить, что уже отправляли.
"""
import json
import os
import time
import requests

from hh_source import fetch_hh_vacancies
from telegram_source import fetch_telegram_vacancies
from rss_source import fetch_rss_vacancies
from scorer import hard_prefilter, score_vacancy
from ai_scorer import ai_score_vacancy, GEMINI_API_KEY
from storage import load_seen, save_seen
from extract import detect_format, detect_location, short_description, detect_target_company

BOT_TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
CHAT_ID = (os.environ.get("TELEGRAM_GROUP_ID") or "").strip()

AI_CALL_DELAY_SECONDS = 4.5


def load_criteria() -> dict:
    with open("criteria.json", "r", encoding="utf-8") as f:
        return json.load(f)


def send_to_telegram(vac: dict, score: int, reason_text: str, fmt: str, location: str, company_match: str | None) -> bool:
    if not (BOT_TOKEN and CHAT_ID):
        print("[bot] Нет TELEGRAM_BOT_TOKEN/TELEGRAM_GROUP_ID — печатаю в консоль вместо отправки:")
        print(vac, score, reason_text, fmt, location, company_match)
        return True

    description = short_description(vac.get("raw_text", ""))
    company_line = f"🇷🇺 Компания из списка HyperCareer: {company_match}\n\n" if company_match else ""

    text = (
        f"🎯 <b>{vac['title']}</b>\n\n"
        f"⭐ Релевантность: {score}/10\n"
        f"🌍 Формат: {fmt}\n"
        f"📍 Локация: {location}\n"
        f"💰 ЗП: {vac.get('salary_text', 'не указана')}\n\n"
        f"{company_line}"
        f"📝 {description}\n\n"
        f"✅ Почему рассмотреть: {reason_text}\n\n"
        f"🔗 {vac['url']}\n"
        f"📌 Источник: {vac['source']}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=15)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[bot] Ошибка отправки в Telegram: {e}")
        return False


def run() -> None:
    criteria = load_criteria()
    seen = load_seen()

    all_vacancies = []
    # hh.ru временно отключён — блокирует запросы с IP GitHub Actions (403), см. README
    # all_vacancies += fetch_hh_vacancies(criteria)
    all_vacancies += fetch_telegram_vacancies(criteria)
    all_vacancies += fetch_rss_vacancies(criteria)

    print(f"[bot] Собрано {len(all_vacancies)} вакансий/сообщений из всех источников.")

    use_ai = bool(GEMINI_API_KEY)
    print(f"[bot] Gemini-скоринг: {'включён' if use_ai else 'выключен (нет GEMINI_API_KEY), работаем на rule-based'}")

    max_ai_calls = criteria.get("max_ai_calls_per_run", 40)
    ai_calls_used = 0
    sent_count = 0
    prefiltered_out = 0

    for vac in all_vacancies:
        if vac["id"] in seen:
            continue
        seen.add(vac["id"])

        passed, reject_reason = hard_prefilter(vac, criteria)
        if not passed:
            prefiltered_out += 1
            continue

        raw_text = vac.get("raw_text", "")
        score = 0
        reason_text = ""
        fmt = detect_format(raw_text)
        location = detect_location(raw_text)
        company_match = detect_target_company(raw_text, criteria.get("target_companies", []))

        ai_result = None
        if use_ai and ai_calls_used < max_ai_calls:
            ai_result = ai_score_vacancy(vac, criteria)
            ai_calls_used += 1
            time.sleep(AI_CALL_DELAY_SECONDS)

        if ai_result:
            score = ai_result["score"]
            reason_text = ai_result["reason"] or "—"
            fmt = ai_result["format"] or fmt
            location = ai_result["location"] or location
        else:
            score, reasons = score_vacancy(vac, criteria)
            reason_text = ", ".join(reasons) if reasons else "—"

        if score >= criteria["min_score_to_send"]:
            if send_to_telegram(vac, score, reason_text, fmt, location, company_match):
                sent_count += 1

    save_seen(seen)
    print(f"[bot] Отсеяно на дешёвом фильтре: {prefiltered_out}")
    print(f"[bot] Обращений к Gemini: {ai_calls_used}")
    print(f"[bot] Отправлено новых вакансий: {sent_count}")


if __name__ == "__main__":
    run()
