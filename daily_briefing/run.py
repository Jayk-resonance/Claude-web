"""Daily Briefing 파이프라인 진입점.

실행: python run.py
      python run.py --dry-run   (Gmail 발송 생략, 이메일 파라미터만 출력)
"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from fetch_news import fetch_articles
from summarize import summarize_articles
from insight import generate_insight
from send_email import build_email


def main(dry_run: bool = False):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"[1/4] 뉴스 수집 중... ({date_str})")
    articles = fetch_articles()
    print(f"      {len(articles)}건 수집 완료")

    print("[2/4] 기사 요약 중... (Haiku 배치)")
    summarized = summarize_articles(articles)
    summarized.sort(key=lambda x: x.get("impact_score", 0), reverse=True)

    print("[3/4] 인사이트 생성 중... (Sonnet)")
    top_article = summarized[0]
    insight_text = generate_insight(top_article)
    print(f"      주목 기사: {top_article['title'][:60]}...")

    print("[4/4] 이메일 파라미터 생성 완료")
    email_params = build_email(summarized, insight_text, top_article, date_str)

    if dry_run:
        print(f"      제목: {email_params['subject']}")
        print(f"      수신자: {email_params['to']}")
        print("      --dry-run 모드: Gmail 발송 생략")
        return email_params

    return email_params


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
