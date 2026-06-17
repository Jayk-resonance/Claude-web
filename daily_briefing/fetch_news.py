"""뉴스 수집 유틸리티.

Direction A (Claude-driven) 에서는 Claude가 Exa/Naver MCP로 직접 수집하므로
fetch_articles()는 호출되지 않는다. get_kst_window()만 시간 범위 참조용으로 사용.
"""
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def get_kst_window() -> tuple[datetime, datetime]:
    """(start, end): 전날 KST 09:00 ~ 오늘 KST 09:00."""
    now = datetime.now(KST).replace(minute=0, second=0, microsecond=0)
    today_9am = now.replace(hour=9)
    if now.hour < 9:
        today_9am -= timedelta(days=1)
    yesterday_9am = today_9am - timedelta(days=1)
    return yesterday_9am, today_9am


def fetch_articles() -> list[dict]:
    """NewsAPI fallback — 유료 플랜 + 로컬 환경에서만 동작."""
    import requests
    from config import NEWS_API_KEY, NEWS_QUERY, MAX_ARTICLES

    start, end = get_kst_window()
    params = {
        "q": NEWS_QUERY,
        "from": start.isoformat(),
        "to": end.isoformat(),
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
