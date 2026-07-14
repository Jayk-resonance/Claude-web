# Daily EV/Battery News Briefing — 루틴 트리거 프롬프트 (백업)

> 이 파일은 스케줄 루틴을 구동하는 **트리거 프롬프트의 백업본**입니다.
> 세션에서 프롬프트 원문을 직접 확인/수정하기 어려운 경우를 대비해, 브랜치에 커밋해 보존합니다.
> 아래 코드블록의 내용은 실제 트리거 프롬프트 원문(verbatim)이며, 수정 시 이 파일을 편집한 뒤 스케줄 설정에 반영하세요.
>
> - 대상 브랜치: `daily-news-briefing-v1`
> - 최종 백업 일자: 2026-07-14 (KST)
> - 상세 실행 문서: 같은 폴더의 `ROUTINE.md` 참조

---

```text
# Daily EV/Battery News Briefing 루틴
## 준비
1. git fetch origin daily-news-briefing-v1 && git checkout daily-news-briefing-v1
2. 새 브랜치 생성 / 커밋 / 푸시 하지 말 것
## 실행 순서
### Step 1 — 시간 범위 확인
daily_briefing/fetch_news.py 의 get_kst_window() 로직을 참고하여
오늘 기준 수집 범위를 계산한다:
- 시작: 전날 KST 09:00
- 종료: 오늘 KST 09:00
### Step 2 — 뉴스 수집 (Exa MCP 우선)
Exa MCP(web_search_exa)로 아래 주제 뉴스를 수집한다 (최대 15건):
- EV battery, electric vehicle battery, 배터리, energy storage, ESS
- 관련 기업: SK On, CATL, LG Energy, Samsung SDI, Panasonic, Tesla, BYD, Ford, GM, Hyundai
- 관련 소재/정책: lithium, nickel, cobalt, IRA, grid storage
Exa 실패 시 Naver Search MCP(search_news)로 대체한다.
※ Naver 사용 시 link가 아닌 originallink를 URL로 사용할 것
수집 후 날짜 필터링:
- 각 기사의 publishedAt을 KST로 변환하여 수집 범위(시작 ~ 종료) 밖의 기사는 제외한다.
- 필터링 후 기사가 8건 미만이면 추가 검색을 수행하여 보충한다.
### Step 3 — 기사 분류 & 점수화
각 기사에 아래 두 항목을 부여한다:
- category: 아래 6개 중 하나
  - EV Maker
  - EV 배터리 기술/산업
  - SK온/배터리 경쟁사
  - 에너지 정책/규제
  - 배터리 광물/공급망
  - ESS/에너지저장
- impact_score (1~10): 산업 전반 영향력 + SK온 직접 관련성 + 시장/정책 파급력 종합
### Step 4 — 인사이트 작성
impact_score 가 가장 높은 기사를 선정하고,
해당 기사에 대해 한국어 인사이트를 600~700단어로 직접 작성한다.
반드시 아래 4개 섹션을 포함할 것:
1. 배경 (왜 이 뉴스가 나왔는가)
2. 핵심 내용 (무슨 일이 일어났는가)
3. 산업 영향 (EV/배터리 산업 전반에 어떤 의미인가)
4. SK온 관점에서의 시사점 (기회/위협/시사점)
인사이트 서식 규칙:
- 4개 소제목은 반드시 "## 배경", "## 핵심 내용", "## 산업 영향", "## SK온 관점에서의 시사점" 형식으로 작성한다.
- 수치, 핵심 키워드, 중요 판단 등 강조할 내용은 **굵게** 마크다운 형식(**text**)으로 표시한다.
### Step 5 — JSON 작성
/tmp/briefing_input.json 을 아래 스키마로 작성한다:
{
  "date_str": "YYYY-MM-DD",
  "articles": [
    {
      "id": 1,
      "title": "...",
      "url": "https://원본-직접-링크",
      "publishedAt": "ISO8601 형식",
      "category": "위 6개 중 하나",
      "summary": "요약 1줄\n요약 2줄\n요약 3줄",
      "impact_score": 8
    }
    // ... 최대 15건
  ],
  "insight": "한국어 인사이트 본문 (4개 섹션, 600~700단어)"
}
### Step 6 — run.py 실행 (수신자에게 직접 발송)
run.py 는 --draft 플래그가 없으면 gmail_sender.send_email_via_api 로
Gmail REST API를 통해 수신자에게 메일을 직접 발송한다.
발송에는 GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN 환경변수가 필요하다.
1. 실행 전, 위 3개 환경변수가 모두 설정되어 있는지 확인한다.
   하나라도 누락이면 발송이 불가하므로 Step 7(폴백)로 바로 넘어간다.
2. 다음을 실행한다 (절대 --draft 를 붙이지 말 것):
   cd daily_briefing && python run.py --input /tmp/briefing_input.json
3. 콘솔에 "[SENT] Gmail API message id: ..." 가 출력되면 발송 성공이다.
   제목 / 수신자 / message id 를 출력하여 완료를 알린다. (이 경우 Step 7은 건너뛴다.)
출력 파일: /tmp/email_output.json (발송 성공/실패와 무관하게 먼저 생성됨)
### Step 7 — 발송 실패 시 폴백 (Gmail 초안)
Step 6 의 자동 발송이 실패한 경우(환경변수 누락, 토큰 만료, [SENT] 미출력, 예외 발생 등)에만
수행한다. 정상 발송된 경우에는 초안을 만들지 말 것.
이미 생성된 /tmp/email_output.json 값으로 Gmail MCP(create_draft)를 호출한다:
- to: /tmp/email_output.json 의 to 값
- subject: /tmp/email_output.json 의 subject 값
- htmlBody: /tmp/email_output.json 의 htmlBody 값 (그대로 사용, 수정 금지)
초안 생성 후, "자동 발송이 실패하여 초안으로 대체했음"을 수동 확인이 필요하다는 점과 함께 명확히 알린다.
```
