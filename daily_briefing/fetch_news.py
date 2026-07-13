"""뉴스 수집 시간 범위 유틸리티.

Direction A (Claude-driven) 에서는 Claude가 Exa/Naver MCP로 직접 뉴스를 수집한다.
이 모듈은 수집 범위 계산용 get_kst_window() 만 제공한다.
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
