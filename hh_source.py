"""
Источник: официальный публичный API hh.ru (api.hh.ru).
Это НЕ скрапинг — открытый, документированный API, им пользуются все легальные джоб-агрегаторы.
Документация: https://api.hh.ru/openapi/redoc
"""
import requests

HH_API_URL = "https://api.hh.ru/vacancies"


def fetch_hh_vacancies(criteria: dict) -> list[dict]:
    """Ищет вакансии на hh.ru по ролям из criteria['roles_keywords'].
    Возвращает список нормализованных словарей: id, title, company, url, salary_text, schedule, snippet, source.
    """
    results = []
    seen_ids = set()
    area = criteria["hh_search"]["area"]
    per_page = criteria["hh_search"]["per_page"]

    for role in criteria["roles_keywords"]:
        params = {
            "text": role,
            "area": area,
            "per_page": per_page,
            "period": 1,  # вакансии за последние сутки — бот и так гоняется по расписанию
            "order_by": "publication_time",
            "schedule": "remote",  # жёсткий фильтр — только удалённые вакансии, зашито в сам запрос
            "employment": criteria["hh_search"].get("employment", ["project", "full"]),
        }
       try:
            resp = requests.get(HH_API_URL, params=params, timeout=20,
                                 headers={"User-Agent": "HH-User-Agent alenanova-job-search/1.0 (alena.bogdanova.job.search@gmail.com)"})
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[hh_source] Ошибка запроса для '{role}': {e}")
            continue

        data = resp.json()
        for item in data.get("items", []):
            vid = item["id"]
            if vid in seen_ids:
                continue
            seen_ids.add(vid)

            salary = item.get("salary")
            if salary:
                lo, hi, cur = salary.get("from"), salary.get("to"), salary.get("currency", "")
                salary_text = f"{lo or ''}–{hi or ''} {cur}".strip()
            else:
                salary_text = "не указана"

            schedule = (item.get("schedule") or {}).get("id", "")
            snippet = " ".join(filter(None, [
                (item.get("snippet") or {}).get("requirement", ""),
                (item.get("snippet") or {}).get("responsibility", ""),
            ]))

            results.append({
                "source": "hh.ru",
                "id": f"hh_{vid}",
                "title": item.get("name", ""),
                "company": (item.get("employer") or {}).get("name", ""),
                "url": item.get("alternate_url", ""),
                "salary_text": salary_text,
                "schedule": schedule,
                "snippet": snippet,
                "raw_text": f"{item.get('name','')} {snippet}",
            })

    return results
