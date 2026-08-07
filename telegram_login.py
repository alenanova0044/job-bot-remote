"""
ОДНОРАЗОВЫЙ скрипт — запускается локально на твоём компьютере, не на Railway.
Логинится в Telegram твоим номером телефона и печатает строку сессии (StringSession),
которую дальше нужно один раз сохранить в переменную окружения TG_SESSION_STRING на Railway.

Как получить TG_API_ID и TG_API_HASH:
1. Зайти на https://my.telegram.org (под своим номером телефона)
2. API Development Tools → создать приложение (любое название)
3. Скопировать api_id и api_hash

Запуск:
    pip install telethon
    python3 telegram_login.py
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("TG_API_ID: "))
api_hash = input("TG_API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print("\n=== Готово ===")
    print("Сохрани это значение в переменную окружения TG_SESSION_STRING на Railway:\n")
    print(session_string)
    print("\nНикому не показывай эту строку — она даёт полный доступ к твоему Telegram-аккаунту.")
