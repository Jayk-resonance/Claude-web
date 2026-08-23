# Daily EV/Battery News Briefing — 루틴 트리거 프롬프트 (백업)

> 이 파일은 스케줄 루틴을 구동하는 **트리거 프롬프트의 백업본**입니다.
> 세션에서 프롬프트 원문을 직접 확인/수정하기 어려운 경우를 대비해, 브랜치에 커밋해 보존합니다.
> 아래 코드블록의 내용은 실제 트리거 프롬프트 원문(verbatim)이며, 수정 시 이 파일을 편집한 뒤 스케줄 설정에 반영하세요.
>
> - 대상 브랜치: `main`
> - 최종 백업 일자: 2026-07-14 (KST)
> - ⚠️ **중요:** 이 트리거 프롬프트는 자기완결형이며, 저장소의 다른 문서를 자동으로 읽지 않습니다.
>   내용을 고쳐도 그대로는 반영되지 않으므로, 수정 시
>   **아래 코드블록을 스케줄 설정의 프롬프트 원문에 반드시 복사·반영**해야 합니다.

---

```text
# Daily EV/Battery News Briefing 루틴
## 준비
1. git fetch origin main && git checkout main
2. 새 브랜치 생성 / 커밋 / 푸시 하지 말 것 (이 브랜치는 읽기 전용으로 실행)
## 실행 순서
### Step 1 — 시간 범위 확인
오늘 기준 수집 범위를 계산한다:
- 시작: 전날 KST 09:00
- 종료: 오늘 KST 09:00
### Step 2 — 뉴스 수집 (Exa 고급검색 우선 · 서버측 날짜/출처 필터)
Exa 고급검색 web_search_advanced_exa (식별자 예: mcp__Exa-----__web_search_advanced_exa)로
아래 주제 뉴스를 수집한다 (최대 15건):
- EV battery, electric vehicle battery, 배터리, energy storage, ESS
- 관련 기업: SK On, CATL, LG Energy, Samsung SDI, Panasonic, Tesla, BYD, Ford, GM, Hyundai
- 관련 소재/정책: lithium, nickel, cobalt, IRA, grid storage
필수 파라미터 (토큰 절감 핵심 — 반드시 지킬 것):
- category: "news"
- startPublishedDate: 수집 시작일 −1일 (day 단위 경계 누락 방지 안전마진)
- endPublishedDate: 오늘 날짜
- type: "auto"
- numResults: 8~10 (토픽당)
- enableSummary: true, summaryQuery: "EV/battery industry impact and key facts"
- textMaxCharacters: 250  ← ⚠️ 반드시 넣을 것. 생략 시 기사 전체 본문(건당 최대 ~17,000자)이
  통째로 반환되어 토큰이 폭증한다. 1처럼 과하게 낮추면 요약도 깨지므로 250 권장.
- excludeDomains: daily_briefing/sources.py 의 BLOCKLIST (콘텐츠팜 하드 차단)
날짜는 파라미터로 거르므로 쿼리에 날짜를 넣지 않아도 된다.
Exa 실패 또는 8건 미달 시 완화 사다리(순서대로):
  1) numResults 15~20으로 재검색 2) startPublishedDate 하루 더 확대(−2일)
  3) BLOCKLIST만 유지한 채 쿼리 다양화 4) Naver Search MCP(search_news) 폴백
  ※ Naver 사용 시 link가 아닌 originallink를 URL로 사용할 것
날짜 재검증 (얇은 안전망 — 서버 필터를 믿고 생략하지 말 것):
- 각 기사의 publishedAt을 KST로 변환하여 수집 범위(시작 ~ 종료) 밖의 기사는 제외한다.
출처 신뢰도 태깅:
- daily_briefing/sources.py 의 classify_domain(url)로 각 기사에 source_tier(TIER1/TIER2/UNKNOWN) 부여.
- BLOCKLIST 도메인이 폴백으로 유입되면 하드 제외.
### Step 3 — 기사 분류 & 점수화
각 기사에 아래 항목을 부여한다:
- category: 아래 6개 중 하나
  - EV Maker
  - EV 배터리 기술/산업
  - SK온/배터리 경쟁사
  - 에너지 정책/규제
  - 배터리 광물/공급망
  - ESS/에너지저장
- impact_score (1~10): 산업 전반 영향력 + SK온 직접 관련성 + 시장/정책 파급력 종합
- source_tier는 impact_score에 약한 가중치로만 반영(UNKNOWN −1 정도), 점수 산정은 모델 판단.
### Step 3.5 — 직전 인사이트 확인 (중복 방지)
인사이트를 고르기 전에 최근 발송분과 같은 기사를 또 뽑지 않도록 확인한다:
- Gmail MCP search_threads 쿼리: subject:"[AI Morning Brief]" newer_than:4d
- 최근 1~2건 스레드를 get_thread로 열어 인사이트 헤더 박스의 기사 제목/URL을 추출.
- 각 직전 인사이트에 대해 사건 단위 정규화 키 topic_key를 뽑는다 (예: "SK온 배터리 결함 리콜").
  topic_key는 URL이 아니라 사건 단위라 다른 매체의 같은 사건도 같은 키로 묶인다.
- Gmail 조회 실패 시(커넥터 미연결/인증 만료 등) 중복 확인만 건너뛰고 나머지는 정상 진행하며,
  "직전 이력 미확인" 상태임을 최종 보고에 명시한다.
### Step 4 — 인사이트 작성
인사이트 기사 선정 규칙:
1) impact_score 내림차순으로 후보를 본다.
2) 인사이트로 뽑는 기사는 반드시 TIER1/TIER2 이면서 독립된 2개 이상 출처가 같은 사건을 보도한
   건이어야 한다. 콘텐츠팜·단독 미확인 보도는 인사이트 불가(기사 테이블에는 실을 수 있음).
3) 최고 impact 기사의 topic_key가 Step 3.5의 직전 인사이트와 같으면, 그다음으로 impact 높은
   다른 topic_key 기사를 인사이트로 선정한다. 단 같은 스토리라도 중대한 신규 전개가 있으면
   허용하되 "후속/새 각도"로 프레이밍한다(예: 리콜 → 배터리팩 교체 비용·주가 반응).
4) 로테이션하는 건 인사이트 1건뿐이며, 그 대형 이슈는 기사 테이블에 계속 실어도 된다.
선정한 기사에 대해 한국어 인사이트를 600~700단어로 직접 작성한다.
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
      "impact_score": 8,
      "source_tier": "TIER1",
      "topic_key": "SK온 배터리 결함 리콜"
    }
    // ... 최대 15건
  ],
  "insight": "한국어 인사이트 본문 (4개 섹션, 600~700단어)"
}
※ source_tier / topic_key 는 내부 판단용 필드로, run.py 가 무시하므로 이메일 렌더링에는 영향 없음.
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
