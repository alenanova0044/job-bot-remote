"""
Источник: RSS-ленты джоб-бордов. Открытый, легальный способ — RSS для этого и придуман.
Стартово подключен Remotive (международный remote-рынок, en) — держим на будущее
под fractional/interim трек, когда подтянется английский. Можно добавлять любые
другие открытые RSS в criteria.json → rss_sources, без изменения кода.
"""
import feedparser


def fetch_rss_vacancies(criteria: dict) -> list[dict]:
    results = []
    for feed_url in criteria.get("rss_sources", []):
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[rss_source] Ошибка чтения {feed_url}: {e}")
            continue

        for entry in feed.entries:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")
            link = getattr(entry, "link", "")
            entry_id = getattr(entry, "id", link) or link

            results.append({
                "source": f"rss:{feed.feed.get('title', feed_url)}",
                "id": f"rss_{abs(hash(entry_id))}",
                "title": title,
                "company": "",
                "url": link,
                "salary_text": "см. описание",
                "schedule": "",
                "snippet": summary[:500],
                "raw_text": f"{title} {summary}",
            })

    return results
