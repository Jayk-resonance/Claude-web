# Claude-web — Daily EV/Battery News Briefing

Codex 예약 작업으로 매일 아침(KST 09:00) EV·배터리·ESS 업계 뉴스를 수집·분류·요약하고 HTML 이메일로 발송하는 자동화 파이프라인입니다.

## 동작 개요

1. 저장소 전용 `$daily-news-briefing` Skill이 검색·선별·중복 방지 규칙을 제공합니다.
2. Codex가 Exa를 우선 사용해 전날 09:00부터 오늘 09:00까지의 뉴스를 수집하고 JSON을 만듭니다.
3. `daily_briefing/run.py`가 입력을 검증하고 외부 텍스트를 이스케이프해 HTML을 생성합니다.
4. 예약 작업이 연결된 Gmail을 통해 `jupiter@sk.com`으로 1회 발송합니다.

## 폴더 구조

```text
.agents/skills/daily-news-briefing/SKILL.md  # Codex 반복 워크플로
daily_briefing/
├── run.py             # JSON 검증 → HTML 빌드, 선택적으로 Gmail API 발송
├── send_email.py      # HTML 이메일 빌더
├── gmail_sender.py    # 로컬 OAuth용 Gmail REST API 발송
├── sources.py         # 출처 신뢰등급·콘텐츠팜 차단 목록
├── config.py          # 수신자·카테고리 설정
└── ROUTINE_PROMPT.md  # 짧은 예약 프롬프트 백업
```

## 수동 렌더링

```bash
python daily_briefing/run.py \
  --input daily_briefing/.runtime/briefing_input.json \
  --output daily_briefing/.runtime/email_output.json \
  --to jupiter@sk.com
```

렌더링이 기본 동작이며 메일을 보내지 않습니다. 로컬 Gmail OAuth 환경변수가 설정되어 있고 직접 발송하려는 경우에만 `--send`를 추가합니다. 예약 작업은 로컬 OAuth 대신 연결된 Gmail을 사용합니다.
