"""
Источник: публичные веб-страницы Telegram-каналов (t.me/s/<канал>).
У любого публичного канала есть открытая страница-превью с последними постами —
это официальная фича Telegram для встраивания, доступна без логина, без api_id,
без session. Поэтому здесь НЕТ Telethon и НЕТ my.telegram.org — просто HTTP-запрос
и разбор HTML.
"""
import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

TME_BASE = "https://t.me/s/"


def fetch_telegram_vacancies(criteria: dict, hours_back: int = 3) -> list[dict]:
    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    for channel in criteria["telegram_channels"]:
        url = f"{TME_BASE}{channel}"
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (compatible; alena-job-bot/1.0)"
            })
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[telegram_source] Ошибка чтения канала {channel}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        messages = soup.select("div.tgme_widget_message")

        for msg in messages:
            time_tag = msg.select_one("time.time")
            if not time_tag or not time_tag.get("datetime"):
                continue
            try:
                msg_dt = datetime.fromisoformat(time_tag["datetime"])
            except ValueError:
                continue
            if msg_dt < cutoff:
                continue

            text_tag = msg.select_one("div.tgme_widget_message_text")
            if not text_tag:
                continue
            text = text_tag.get_text("\n", strip=True)
            if not text:
                continue

            data_post = msg.get("data-post")
            post_id = data_post.split("/")[-1] if data_post else re.sub(r"\W+", "", text[:30])

            results.append({
                "source": f"tg:@{channel}",
                "id": f"tg_{channel}_{post_id}",
                "title": text.split("\n")[0][:120],
                "company": "",
                "url": f"https://t.me/{channel}/{post_id}",
                "salary_text": "см. текст",
                "schedule": "",
                "snippet": text[:500],
                "raw_text": text,
            })

    return results
