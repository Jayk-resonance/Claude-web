"""Daily Briefing pipeline — Claude-driven HTML builder.

Claude Code가 이 루틴을 다음 순서로 실행한다:

  1. 수집 시간 범위 확인 (전날 KST 09:00 → 오늘 KST 09:00)
  2. Exa MCP (우선) 또는 Naver Search MCP (fallback) 으로 뉴스 수집
     - Naver 사용 시: link 가 아닌 originallink 사용 (리다이렉트 방지)
  3. 각 기사에 category (config.CATEGORIES 중 하나) 와 impact_score (1-10) 부여
  4. 최고 impact_score 기사 선정 후 한국어 인사이트 작성 (4개 섹션):
       배경 / 핵심 내용 / 산업 영향 / SK온 관점에서의 시사점
  5. /tmp/briefing_input.json 작성 (하단 INPUT SCHEMA 참조)
  6. python run.py --input /tmp/briefing_input.json 실행
     → HTML 이메일 빌드 후 gmail_sender.send_email_via_api 로 Gmail API 자동 발송
       (--draft 플래그 사용 시 발송 없이 빌드만 수행)
  7. 발송 실패 시 /tmp/email_output.json 값으로 Gmail MCP create_draft 폴백

INPUT SCHEMA:
{
  "date_str": "2026-06-17",
  "articles": [
    {
      "id": 1,
      "title": "...",
      "url": "https://원본-직접-링크",
      "publishedAt": "2026-06-16T10:00:00+09:00",
      "category": "EV Maker",
      "summary": "요약 1줄\n요약 2줄\n요약 3줄",
      "impact_score": 8
    }
  ],
  "insight": "한국어 인사이트 본문 (4개 섹션, ~600단어)..."
}
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone
from send_email import build_email

KST = timezone(timedelta(hours=9))


def main():
    if "--input" not in sys.argv:
        print(__doc__)
        sys.exit(1)

    idx = sys.argv.index("--input")
    input_file = sys.argv[idx + 1]

    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    date_str = data.get("date_str") or datetime.now(KST).strftime("%Y-%m-%d")
    articles = sorted(data["articles"], key=lambda x: x.get("impact_score", 0), reverse=True)
    insight_text = data["insight"]
    top_article = articles[0]

    email_params = build_email(articles, insight_text, top_article, date_str)

    output = "/tmp/email_output.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(email_params, f, ensure_ascii=False, indent=2)

    print(f"[OK] 제목: {email_params['subject']}")
    print(f"     수신자: {email_params['to']}")
    print(f"     HTML → {output}")

    if "--draft" not in sys.argv:
        from gmail_sender import send_email_via_api
        msg_id = send_email_via_api(
            email_params["to"], email_params["subject"], email_params["htmlBody"]
        )
        print(f"[SENT] Gmail API message id: {msg_id}")

    return email_params


if __name__ == "__main__":
    main()
