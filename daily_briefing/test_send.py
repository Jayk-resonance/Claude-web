"""Gmail API 자동발송 점검용 1회성 테스트.

본인 주소로만 테스트 메일 1통을 보낸다. 실제 브리핑 수신자에게는 보내지 않는다.
환경변수(GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN)가
주입된 세션에서 실행할 것:

    cd daily_briefing && python test_send.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from gmail_sender import send_email_via_api

TEST_TO = ["jupiter@sk.com"]
REQUIRED = ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")


def main():
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        print("[FAIL] 누락된 환경변수:", ", ".join(missing))
        sys.exit(1)

    try:
        msg_id = send_email_via_api(
            TEST_TO,
            "[테스트] Gmail 자동발송 점검",
            "<p>자동발송 연결 테스트 성공 ✅<br>이 메일이 보이면 무인 발송 준비 완료입니다.</p>",
        )
    except Exception as e:
        print(f"[FAIL] 발송 실패: {type(e).__name__}: {e}")
        sys.exit(1)

    print(f"[OK] 테스트 메일 발송 완료 → {TEST_TO[0]} / message id: {msg_id}")


if __name__ == "__main__":
    main()
