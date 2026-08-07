"""
Источник: публичные Telegram-каналы с вакансиями.
Читаем как пользователь (Telethon), потому что обычный бот НЕ может читать чужие каналы,
на которые не подписан как админ. Один раз логинимся телефоном локально — дальше работает
по сохранённой сессии (см. telegram_login.py и README).
"""
import os
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

TG_API_ID = os.environ.get("TG_API_ID")
TG_API_HASH = os.environ.get("TG_API_HASH")
TG_SESSION_STRING = os.environ.get("TG_SESSION_STRING")


def fetch_telegram_vacancies(criteria: dict, hours_back: int = 2) -> list[dict]:
    """Читает последние сообщения из списка каналов criteria['telegram_channels'].
    Каждое сообщение целиком считается одним "кандидатом на вакансию" —
    дальше его текст прогоняется через тот же скоринг, что и структурированные вакансии hh.ru.
    """
    if not (TG_API_ID and TG_API_HASH and TG_SESSION_STRING):
        print("[telegram_source] Нет TG_API_ID/TG_API_HASH/TG_SESSION_STRING — источник пропущен.")
        return []

    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    with TelegramClient(StringSession(TG_SESSION_STRING), int(TG_API_ID), TG_API_HASH) as client:
        for channel in criteria["telegram_channels"]:
            try:
                for msg in client.iter_messages(channel, limit=100):
                    if msg.date < cutoff:
                        break
                    if not msg.text:
                        continue
                    results.append({
                        "source": f"tg:@{channel}",
                        "id": f"tg_{channel}_{msg.id}",
                        "title": msg.text.strip().split("\n")[0][:120],
                        "company": "",
                        "url": f"https://t.me/{channel}/{msg.id}",
                        "salary_text": "см. текст",
                        "schedule": "",
                        "snippet": msg.text.strip()[:500],
                        "raw_text": msg.text,
                    })
            except Exception as e:
                print(f"[telegram_source] Ошибка чтения канала {channel}: {e}")
                continue

    return results
