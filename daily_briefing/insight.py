import anthropic
from config import ANTHROPIC_API_KEY, SONNET_MODEL


def generate_insight(article: dict) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""다음 기사에 대해 1페이지 분량(600~700단어)의 인사이트를 한국어로 작성하라.

구성:
1. 배경 (왜 이 뉴스가 나왔는가)
2. 핵심 내용 (무슨 일이 일어났는가)
3. 산업 영향 (EV/배터리 산업 전반에 어떤 의미인가)
4. SK온 관점에서의 시사점 (SK온에게 기회/위협/시사점은 무엇인가) ← 반드시 포함

기사 제목: {article["title"]}
카테고리: {article["category"]}
요약: {article["summary"]}
링크: {article["url"]}"""

    message = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
