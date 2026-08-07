"""
Хранит id уже отправленных вакансий, чтобы не слать дубли при каждом запуске.
На Railway путь /data должен быть подключенным Volume (см. README) — иначе
при каждом деплое файл будет обнуляться.
"""
import json
import os

STORAGE_PATH = os.environ.get("STORAGE_PATH", "/data/seen_jobs.json")


def load_seen() -> set:
    if not os.path.exists(STORAGE_PATH):
        return set()
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(seen: set) -> None:
    os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
    # Не даём файлу расти бесконечно — держим последние 5000 id
    trimmed = list(seen)[-5000:]
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False)
