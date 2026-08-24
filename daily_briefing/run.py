"""Validate briefing JSON, render HTML, and optionally send through Gmail API."""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))

from config import CATEGORIES
from send_email import build_email
from sources import classify_domain

KST = timezone(timedelta(hours=9))
APPROVED_RECIPIENT = "jupiter@sk.com"
DEFAULT_OUTPUT = Path(tempfile.gettempdir()) / "email_output.json"
REQUIRED_INSIGHT_SECTIONS = (
    "## 배경",
    "## 핵심 내용",
    "## 산업 영향",
    "## SK온 관점에서의 시사점",
)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Briefing input JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Rendered email JSON")
    parser.add_argument("--to", default=APPROVED_RECIPIENT, help="Approved recipient")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send through the local Gmail API credentials; rendering is the safe default",
    )
    return parser.parse_args(argv)


def validate_input(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("입력은 JSON 객체여야 합니다.")

    articles = data.get("articles")
    if not isinstance(articles, list) or len(articles) < 8:
        raise ValueError("articles에는 기사 8건 이상이 필요합니다.")
    if len(articles) > 15:
        raise ValueError("articles는 최대 15건까지 허용됩니다.")
    if not isinstance(data.get("insight"), str) or not data["insight"].strip():
        raise ValueError("insight가 비어 있습니다.")
    missing_sections = [
        section for section in REQUIRED_INSIGHT_SECTIONS if section not in data["insight"]
    ]
    if missing_sections:
        raise ValueError(f"insight 필수 섹션이 없습니다: {', '.join(missing_sections)}")

    date_str = data.get("date_str")
    if date_str:
        datetime.strptime(date_str, "%Y-%m-%d")

    seen_urls = set()
    for index, article in enumerate(articles, start=1):
        if not isinstance(article, dict):
            raise ValueError(f"기사 {index}가 객체가 아닙니다.")
        for field in ("title", "url", "publishedAt", "category", "summary", "impact_score"):
            if field not in article or article[field] in (None, ""):
                raise ValueError(f"기사 {index}의 {field}가 비어 있습니다.")

        parsed = urlparse(str(article["url"]))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"기사 {index}의 URL은 http/https 원문 링크여야 합니다.")
        if classify_domain(str(article["url"])) == "BLOCKLIST":
            raise ValueError(f"기사 {index}의 URL은 차단된 출처입니다.")
        if article["url"] in seen_urls:
            raise ValueError(f"기사 {index}의 URL이 중복되었습니다.")
        seen_urls.add(article["url"])

        if article["category"] not in CATEGORIES:
            raise ValueError(f"기사 {index}의 category가 허용 목록에 없습니다.")
        score = article["impact_score"]
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10:
            raise ValueError(f"기사 {index}의 impact_score는 1~10 정수여야 합니다.")
        datetime.fromisoformat(str(article["publishedAt"]).replace("Z", "+00:00"))


def main(argv=None):
    args = _parse_args(argv)
    if args.to != APPROVED_RECIPIENT:
        raise ValueError(f"현재 허용된 수신자는 {APPROVED_RECIPIENT}뿐입니다.")

    with args.input.open(encoding="utf-8") as file:
        data = json.load(file)
    validate_input(data)

    date_str = data.get("date_str") or datetime.now(KST).strftime("%Y-%m-%d")
    articles = sorted(data["articles"], key=lambda item: item["impact_score"], reverse=True)
    email_params = build_email(
        articles,
        data["insight"],
        articles[0],
        date_str,
        recipients=[args.to],
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(email_params, file, ensure_ascii=False, indent=2)

    print(f"[OK] 제목: {email_params['subject']}")
    print(f"     수신자: {email_params['to']}")
    print(f"     HTML → {args.output}")

    if args.send:
        from gmail_sender import send_email_via_api

        message_id = send_email_via_api(
            email_params["to"],
            email_params["subject"],
            email_params["textBody"],
            email_params["htmlBody"],
        )
        print(f"[SENT] Gmail API message id: {message_id}")

    return email_params


if __name__ == "__main__":
    main()
