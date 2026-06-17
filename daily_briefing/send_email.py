def build_email(articles: list[dict], insight_text: str, top_article: dict, date_str: str) -> dict:
    """Gmail MCP create_draft에 전달할 이메일 파라미터를 반환한다."""
    from config import RECIPIENT_EMAIL

    subject = f"[AI Morning Brief] {date_str} 배터리 (EV/ESS) 핵심 동향"

    article_rows = ""
    for a in articles:
        summary = a.get("summary", "").replace("\\n", "<br>")
        article_rows += f"""
        <tr>
          <td style="padding:8px;border:1px solid #ddd;color:#555;font-size:12px">{a.get("category","")}</td>
          <td style="padding:8px;border:1px solid #ddd;font-size:13px">
            <a href="{a.get('url','')}" style="color:#1a73e8;text-decoration:none">{a['title']}</a><br>
            <span style="color:#666;font-size:12px">{summary}</span>
          </td>
        </tr>"""

    insight_html = "".join(
        f"<p style='margin:0 0 12px 0'>{line}</p>"
        for line in insight_text.split("\n") if line.strip()
    )

    html_body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;color:#333">

<h2 style="color:#1a1a1a;border-bottom:2px solid #1a73e8;padding-bottom:8px">
  📰 AI Morning Brief — {date_str}
</h2>
<p style="color:#888;font-size:12px">EV · 배터리 · ESS 핵심 동향 | AI 자동생성 브리핑</p>

<h3 style="color:#333;margin-top:24px">오늘의 주요 기사</h3>
<table style="width:100%;border-collapse:collapse">
  <tr style="background:#f5f5f5">
    <th style="padding:8px;border:1px solid #ddd;text-align:left;width:140px">카테고리</th>
    <th style="padding:8px;border:1px solid #ddd;text-align:left">제목 / 요약</th>
  </tr>
  {article_rows}
</table>

<h3 style="color:#333;margin-top:32px">🔍 주목 기사 인사이트</h3>
<p style="background:#f0f4ff;padding:12px;border-left:4px solid #1a73e8;font-weight:bold">
  {top_article['title']}
  <span style="font-weight:normal;color:#888;font-size:12px"> | {top_article.get('category','')} | Impact Score: {top_article.get('impact_score','')}/10</span>
</p>
<div style="line-height:1.8">
  {insight_html}
</div>

<hr style="margin-top:40px;border:none;border-top:1px solid #eee">
<p style="color:#aaa;font-size:11px;text-align:center">
  본 브리핑은 Claude AI가 자동 생성한 콘텐츠입니다. | {date_str} 09:00 기준
</p>
</body></html>"""

    return {
        "to": [RECIPIENT_EMAIL],
        "subject": subject,
        "htmlBody": html_body,
    }
