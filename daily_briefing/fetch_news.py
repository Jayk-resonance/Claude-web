import requests
from datetime import datetime, timedelta, timezone
from config import NEWS_API_KEY, NEWS_QUERY, MAX_ARTICLES


def fetch_articles() -> list[dict]:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    today_9am = now.replace(hour=9)
    if now.hour < 9:
        today_9am -= timedelta(days=1)
    yesterday_9am = today_9am - timedelta(days=1)

    params = {
        "q": NEWS_QUERY,
        "from": yesterday_9am.isoformat(),
        "to": today_9am.isoformat(),
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": MAX_ARTICLES,
        "apiKey": NEWS_API_KEY,
    }

    resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    articles = []
    for i, a in enumerate(data.get("articles", []), 1):
        description = (a.get("description") or "")[:200]
        articles.append({
            "id": i,
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "publishedAt": a.get("publishedAt", ""),
            "description": description,
        })

    return articles
