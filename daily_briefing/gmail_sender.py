"""Gmail API 발송 유틸리티 (HTTPS 기반).

원격 실행 환경은 SMTP(587/465)가 차단되어 있으나 HTTPS는 허용되므로,
SMTP 대신 Gmail REST API로 메일을 발송한다.

필요한 환경변수 (OAuth, gmail.send 스코프):
  GMAIL_CLIENT_ID      OAuth 클라이언트 ID
  GMAIL_CLIENT_SECRET  OAuth 클라이언트 시크릿
  GMAIL_REFRESH_TOKEN  gmail.send 스코프로 발급한 refresh token

requests 는 HTTPS_PROXY / REQUESTS_CA_BUNDLE 환경변수를 자동으로 따르므로
프록시 환경에서도 별도 설정 없이 동작한다.
"""
import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TOKEN_URL = "https://oauth2.googleapis.com/token"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _get_access_token() -> str:
    """refresh token 으로 단기 access token 을 발급받는다."""
    import requests

    client_id = os.environ["GMAIL_CLIENT_ID"]
    client_secret = os.environ["GMAIL_CLIENT_SECRET"]
    refresh_token = os.environ["GMAIL_REFRESH_TOKEN"]

    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def build_mime_message(
    to: list[str], subject: str, text_body: str, html_body: str
) -> MIMEMultipart:
    """텍스트와 HTML을 모두 담은 multipart/alternative 메시지를 만든다."""
    msg = MIMEMultipart("alternative")
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def send_email_via_api(
    to: list[str], subject: str, text_body: str, html_body: str
) -> str:
    """Gmail API 로 multipart/alternative 메일을 발송하고 message id 를 반환한다."""
    import requests

    access_token = _get_access_token()
    msg = build_mime_message(to, subject, text_body, html_body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("id", "")
