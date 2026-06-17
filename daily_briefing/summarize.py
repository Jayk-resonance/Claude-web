import json
import anthropic
from config import ANTHROPIC_API_KEY, HAIKU_MODEL, CATEGORIES


def summarize_articles(articles: list[dict]) -> list[dict]:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    articles_text = "\n\n".join(
        f'[{a["id"]}] 제목: {a["title"]}\n리드: {a["description"]}'
        for a in articles
    )

    categories_str = ", ".join(CATEGORIES)

    prompt = f"""아래 뉴스 기사들을 분석하여 JSON 배열로만 반환하라. 설명 없이 JSON만 출력.

각 항목 형식:
{{"id": <int>, "title": "<제목>", "summary": "<3줄 요약, 줄바꿈은 \\n>", "category": "<카테고리>", "impact_score": <1-10>}}

카테고리는 다음 중 하나: {categories_str}

impact_score 기준: 산업 전반에 미치는 영향력, SK온과의 직접 관련성, 시장 규모 및 정책 파급력

기사 목록:
{articles_text}"""

    message = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # strip markdown code block if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    summarized = json.loads(raw)

    url_map = {a["id"]: a["url"] for a in articles}
    published_map = {a["id"]: a["publishedAt"] for a in articles}
    for item in summarized:
        item["url"] = url_map.get(item["id"], "")
        item["publishedAt"] = published_map.get(item["id"], "")

    return summarized
