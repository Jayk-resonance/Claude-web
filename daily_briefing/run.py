"""Daily Briefing 파이프라인 진입점.

실행: python run.py
      python run.py --dry-run   (Gmail 발송 생략)
"""
import sys
import os
from datetime import datetime, timezone

# 현재 디렉터리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from fetch_news import fetch_articles
from summarize import summarize_articles
from insight import generate_insight
from render import render_report
from send_email import send_briefing


def main(dry_run: bool = False):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[1/5] 뉴스 수집 중... ({date_str})")
    articles = fetch_articles()
    print(f"      {len(articles)}건 수집 완료")

    print("[2/5] 기사 요약 중... (Haiku 배치)")
    summarized = summarize_articles(articles)
    summarized.sort(key=lambda x: x.get("impact_score", 0), reverse=True)

    print("[3/5] 인사이트 생성 중... (Sonnet)")
    top_article = summarized[0]
    insight_text = generate_insight(top_article)
    print(f"      주목 기사: {top_article['title'][:60]}...")

    print("[4/5] Word 리포트 생성 중...")
    docx_path = render_report(summarized, top_article, insight_text, date_str)
    print(f"      저장 완료: {docx_path}")

    if dry_run:
        print("[5/5] --dry-run 모드: Gmail 발송 생략")
        return

    print("[5/5] Gmail 발송 준비 중...")
    email_params = send_briefing(docx_path, summarized, date_str)
    print(f"      수신자: {email_params['to']}")
    print("      *** Gmail MCP 도구를 통해 발송하려면 Claude Code 세션에서 실행하세요. ***")
    print(f"      제목: {email_params['subject']}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
