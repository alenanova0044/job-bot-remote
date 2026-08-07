"""
Главный скрипт — запускается по расписанию (см. README, Railway Cron).
Один проход: собрать вакансии из всех источников → оценить → отправить новые
подходящие в Telegram-группу → сохранить, что уже отправляли.
"""
import json
import os
import requests

from hh_source import fetch_hh_vacancies
from telegram_source import fetch_telegram_vacancies
from rss_source import fetch_rss_vacancies
from scorer import score_vacancy
from storage import load_seen, save_seen

BOT_TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
CHAT_ID = (os.environ.get("TELEGRAM_GROUP_ID") or "").strip()


def load_criteria() -> dict:
    with open("criteria.json", "r", encoding="utf-8") as f:
        return json.load(f)


def send_to_telegram(vac: dict, score: int, reasons: list[str]) -> bool:
    if not (BOT_TOKEN and CHAT_ID):
        print("[bot] Нет TELEGRAM_BOT_TOKEN/TELEGRAM_GROUP_ID — печатаю в консоль вместо отправки:")
        print(vac, score, reasons)
        return True

    text = (
        f"🎯 <b>{vac['title']}</b>\n"
        f"{vac.get('company', '')}\n"
        f"⭐ Релевантность: {score}/10 — {', '.join(reasons)}\n"
        f"💰 {vac.get('salary_text', 'не указана')}\n"
        f"🔗 {vac['url']}\n"
        f"📍 Источник: {vac['source']}"
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
    all_vacancies += fetch_hh_vacancies(criteria)
    all_vacancies += fetch_telegram_vacancies(criteria)
    all_vacancies += fetch_rss_vacancies(criteria)

    print(f"[bot] Собрано {len(all_vacancies)} вакансий/сообщений из всех источников.")

    sent_count = 0
    for vac in all_vacancies:
        if vac["id"] in seen:
            continue

        score, reasons = score_vacancy(vac, criteria)
        seen.add(vac["id"])  # помечаем просмотренным в любом случае, чтобы не пересчитывать

        if score >= criteria["min_score_to_send"]:
            if send_to_telegram(vac, score, reasons):
                sent_count += 1

    save_seen(seen)
    print(f"[bot] Отправлено новых вакансий: {sent_count}")


if __name__ == "__main__":
    run()
