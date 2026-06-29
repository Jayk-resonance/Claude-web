"""Multi-agent 토론(Debate).

하나의 논쟁적 질문을 찬성(PRO)/반대(CON) 양측 관점으로 검토하고, 중립 심판(JUDGE)이
균형 잡힌 결론을 내린다. 역할별 system 프롬프트가 다른 순차 messages.create() 호출이며,
PRO/CON 변론은 Sonnet + 웹검색, 종합 판단만 Opus가 맡는다.

실행: python debate.py --topic "중국 배터리 업체가 미국 FEOC/PFE 규제를 우회해 ESS를 생산할 수 있는가?"
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))

import anthropic
from config import ANTHROPIC_API_KEY, SONNET_MODEL, OPUS_MODEL

# Sonnet 4.6 / Opus 4.8 은 _20260209(동적 필터링) 지원
WEB_SEARCH = [{"type": "web_search_20260209", "name": "web_search"}]

PRO_SYSTEM = (
    "당신은 토론의 '찬성(PRO)' 측 변론자다. 질문에 긍정 입장을 가장 설득력 있게 변론하라. "
    "구체적 근거·메커니즘·사례와 출처를 제시하고, 가장 강한 반대 논거를 미리 반박하라. "
    "입장을 흐리지 말고 일관되게 찬성하라."
)

CON_SYSTEM = (
    "당신은 토론의 '반대(CON)' 측 변론자다. 질문에 부정 입장을 가장 설득력 있게 변론하라. "
    "구체적 근거·메커니즘·사례와 출처를 제시하고, 가장 강한 찬성 논거를 미리 반박하라. "
    "입장을 흐리지 말고 일관되게 반대하라."
)

SYNTHESIS_SYSTEM = (
    "당신은 중립적인 토론 심판(JUDGE)이다. 양측 주장을 읽고 각 측의 강점과 약점을 평가한 뒤 "
    "증거에 기반한 균형 잡힌 결론을 제시하라. 미리 기울지 말고 불확실성은 명시하라. 발언 순서나 "
    "마지막 발언권은 주장의 강도를 의미하지 않는다 — 오직 논거의 질과 근거로만 판단하라. "
    "출력: (1) 찬성 핵심·강점·약점 (2) 반대 핵심·강점·약점 (3) 종합 판단과 근거 (4) 남은 불확실성."
)


def _ask(model: str, system: str, prompt: str, tools=None, max_tokens: int = 2500) -> str:
    """단일 역할 호출. 역할별로 model 을 받는다. 웹검색 server-tool 의 pause_turn 루프와
    text 블록 추출을 처리한다."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": prompt}]
    while True:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=tools or [],
            messages=messages,
        )
        if message.stop_reason == "pause_turn":  # server-tool 10회 한도 → 재개
            messages.append({"role": "assistant", "content": message.content})
            continue
        break
    # adaptive thinking + web_search 환경에서 content[0] 은 thinking/tool 블록일 수 있으므로
    # 반드시 text 블록만 모은다 ([0] 인덱싱 금지)
    return "".join(b.text for b in message.content if b.type == "text").strip()


def argue(topic: str, system: str) -> str:
    return _ask(
        SONNET_MODEL,
        system,
        f"질문: {topic}\n\n당신의 입장에서 근거를 갖춘 논거를 전개하라. "
        "웹 검색으로 최신 사실·규제·사례를 확인하고 출처를 제시하라.",
        tools=WEB_SEARCH,
    )


def rebut(topic: str, system: str, opponent: str, own_prior: str = None) -> str:
    parts = [f"질문: {topic}", f"[상대 측 주장]\n{opponent}"]
    if own_prior:
        parts.append(f"[당신의 이전 주장]\n{own_prior}")
    parts.append(
        "상대의 주장을 구체적으로 반박하고 당신의 입장을 강화하라. "
        "필요하면 웹 검색으로 근거를 확인하라."
    )
    return _ask(SONNET_MODEL, system, "\n\n".join(parts), tools=WEB_SEARCH)


def synthesize(topic: str, pro_1: str, con_1: str, pro_2: str, con_2: str) -> str:
    prompt = (
        f"질문: {topic}\n\n[찬성 입론]\n{pro_1}\n\n[반대 반박]\n{con_1}\n\n"
        f"[찬성 재반박]\n{pro_2}\n\n[반대 재반박]\n{con_2}\n\n"
        "위 토론 전체를 평가하고 결론을 내려라."
    )
    return _ask(OPUS_MODEL, SYNTHESIS_SYSTEM, prompt, max_tokens=3000)  # JUDGE → Opus, 검색 없음


def run_debate(topic: str) -> dict:
    print("[1/5] PRO 입론 중... (Sonnet + 웹검색)", file=sys.stderr)
    pro_1 = argue(topic, PRO_SYSTEM)
    print("[2/5] CON 반박 중... (Sonnet + 웹검색)", file=sys.stderr)
    con_1 = rebut(topic, CON_SYSTEM, pro_1)
    print("[3/5] PRO 재반박 중... (Sonnet + 웹검색)", file=sys.stderr)
    pro_2 = rebut(topic, PRO_SYSTEM, con_1, own_prior=pro_1)
    print("[4/5] CON 재반박 중... (Sonnet + 웹검색)", file=sys.stderr)
    con_2 = rebut(topic, CON_SYSTEM, pro_2, own_prior=con_1)
    print("[5/5] JUDGE 종합 중... (Opus)", file=sys.stderr)
    verdict = synthesize(topic, pro_1, con_1, pro_2, con_2)
    return {
        "topic": topic,
        "pro_1": pro_1,
        "con_1": con_1,
        "pro_2": pro_2,
        "con_2": con_2,
        "verdict": verdict,
    }


def print_markdown(r: dict) -> None:
    print(f"# 토론: {r['topic']}\n")
    print(f"## 찬성 입론 (PRO)\n\n{r['pro_1']}\n")
    print(f"## 반대 반박 (CON)\n\n{r['con_1']}\n")
    print(f"## 찬성 재반박 (PRO)\n\n{r['pro_2']}\n")
    print(f"## 반대 재반박 (CON)\n\n{r['con_2']}\n")
    print(f"## 종합 판단 (JUDGE)\n\n{r['verdict']}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-agent 토론")
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    result = run_debate(args.topic)
    print_markdown(result)
