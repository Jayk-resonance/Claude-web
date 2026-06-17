import base64
import os


def send_briefing(docx_path: str, articles: list[dict], date_str: str):
    """Gmail MCP를 통해 브리핑 이메일을 발송한다.

    이 함수는 Claude Code 세션 내에서 Gmail MCP 도구를 직접 호출하는 대신,
    run.py 파이프라인에서 MCP 도구를 시퀀셜하게 호출할 수 있도록
    필요한 파라미터를 딕셔너리로 반환한다.
    """
    from config import RECIPIENT_EMAIL, SENDER_EMAIL

    subject = f"[Daily Briefing] {date_str} EV/Battery 주요 동향"

    lines = [f"안녕하세요,\n\n{date_str} EV/Battery Daily Briefing입니다.\n"]
    for a in articles:
        summary = a.get("summary", "").replace("\\n", " ")
        lines.append(f'[{a["id"]}] [{a.get("category","")}] {a["title"]}')
        lines.append(f'    {summary}')
        lines.append(f'    {a.get("url","")}\n')
    lines.append("\n첨부 Word 파일에서 주목 기사 인사이트를 확인하세요.\n\n감사합니다.")

    body = "\n".join(lines)

    with open(docx_path, "rb") as f:
        attachment_b64 = base64.b64encode(f.read()).decode()

    return {
        "to": RECIPIENT_EMAIL,
        "subject": subject,
        "body": body,
        "attachment_path": docx_path,
        "attachment_b64": attachment_b64,
        "attachment_filename": os.path.basename(docx_path),
    }
