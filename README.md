# Claude-web — Daily EV/Battery News Briefing

Claude Code on the Web의 **Routine** 기능으로 매일 아침(KST 09:00) EV·배터리·ESS 업계 핵심 뉴스를 자동으로 수집·분류·요약하고, HTML 이메일로 수신자에게 발송하는 자동화 파이프라인입니다.

## 동작 개요

매일 정해진 시각에 Claude가 다음을 자동 수행합니다.

1. **수집 범위 계산** — 전날 09:00 ~ 오늘 09:00 (KST)
2. **뉴스 수집** — Exa MCP(우선) / Naver Search MCP(폴백), 최대 15건
3. **분류 & 점수화** — 6개 카테고리 + 임팩트 점수(1~10)
4. **심층 인사이트** — 최고 점수 기사에 대해 SK온 관점 한국어 분석(600~700단어)
5. **JSON 생성 → HTML 이메일 빌드**
6. **Gmail API로 수신자에게 직접 발송** (실패 시 Gmail 초안으로 폴백)

## 폴더 구조

```
daily_briefing/
├── run.py             # 진입점: JSON → HTML 빌드 → Gmail API 발송
├── send_email.py      # HTML 이메일 빌더
├── gmail_sender.py    # Gmail REST API 발송
├── sources.py         # 출처 신뢰등급(TIER1/TIER2)·콘텐츠팜 차단 목록
├── config.py          # 수신자·카테고리 등 설정
└── ROUTINE_PROMPT.md  # 루틴 트리거 프롬프트 원본 (7단계 상세)
```

## 셋업

1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
2. 환경변수 설정 (`.env.example` 참고) — Gmail API 발송용 OAuth 자격증명
   - `GMAIL_CLIENT_ID`
   - `GMAIL_CLIENT_SECRET`
   - `GMAIL_REFRESH_TOKEN`

## 수동 실행

```bash
cd daily_briefing
python run.py --input /tmp/briefing_input.json          # 발송
python run.py --input /tmp/briefing_input.json --draft  # 발송 없이 빌드만
```

자세한 루틴 실행 절차는 [`daily_briefing/ROUTINE_PROMPT.md`](daily_briefing/ROUTINE_PROMPT.md)를 참고하세요.
이 파일이 매일 실행되는 스케줄 루틴의 프롬프트 원본입니다.
