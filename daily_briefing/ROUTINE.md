# Daily EV/Battery News Briefing 루틴

> **목적:** 매일 오전 KST 09:00, 전날 09:00부터 당일 09:00 사이에 발행된 EV·배터리·ESS 핵심 뉴스를 수집·분류·요약하고, HTML 이메일로 수신자에게 자동 발송한다.
>
> **독자:** 이 문서를 읽는 생성형 AI. 아래 7단계를 순서대로 수행하면 된다.

---

## 사전 준비

### 브랜치 체크아웃
```bash
git fetch origin daily-news-briefing-v1
git checkout daily-news-briefing-v1
```
> **주의:** 새 브랜치 생성·커밋·푸시 금지. 이 브랜치에서 읽기만 한다.

### 필요 환경 변수 (이메일 발송용)
| 변수명 | 설명 |
|---|---|
| `GMAIL_CLIENT_ID` | Gmail OAuth 클라이언트 ID |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth 클라이언트 시크릿 |
| `GMAIL_REFRESH_TOKEN` | Gmail 리프레시 토큰 |

Step 6 실행 전 세 변수가 모두 설정되어 있는지 확인한다. 하나라도 없으면 Step 6을 건너뛰고 Step 7(초안 폴백)을 수행한다.

### 수신자 / 발신자 (config.py 기준)
- **수신자:** `jupiter@sk.com`, `hc.yoon@sk.com`, `lee.hojeong@sk.com`, `hoyoonlee@sk.com`, `jslim27@sk.com`
- **발신자:** `kjwgv1442@gmail.com`

---

## Step 1 — 수집 시간 범위 확인

`daily_briefing/fetch_news.py`의 `get_kst_window()` 로직 참고:

```
수집 시작: 전날 KST 09:00
수집 종료: 오늘 KST 09:00
```

KST = UTC+9이므로 UTC 기준으로는:
```
수집 시작: 전날 UTC 00:00
수집 종료: 오늘 UTC 00:00
```

예) 오늘이 2026-07-01이면 → 2026-06-30T00:00:00Z ~ 2026-07-01T00:00:00Z

---

## Step 2 — 뉴스 수집 (Exa 고급검색: 서버측 날짜·출처 필터)

> **핵심 변경:** 예전에는 뉴스를 잔뜩 긁어온 뒤 인컨텍스트로 날짜를 걸렀지만,
> 이제는 **Exa 고급검색이 서버에서 날짜·출처·본문길이를 미리 걸러** 반환한다.
> 창밖 기사·콘텐츠팜·전체 본문을 애초에 안 받아오므로 Step 2 토큰이 대폭 줄어든다
> (실측 기준 약 85% 감소).

### 2-A. Exa 고급검색 사용 (우선)

`web_search_advanced_exa` 툴(식별자 예: `mcp__Exa-----__web_search_advanced_exa`)로
아래 토픽을 **병렬** 검색한다 (총 최대 15건 목표).

**필수 파라미터 — 토큰 절감의 핵심이므로 반드시 지킨다:**

| 파라미터 | 값 | 이유 |
|---|---|---|
| `category` | `"news"` | 뉴스만 |
| `startPublishedDate` | **수집 시작일 −1일** (예: 07-13 창 → `"2026-07-12"`) | Exa 날짜는 day 단위·크롤링 추정값 → 경계 누락 방지 안전마진 |
| `endPublishedDate` | 오늘 날짜 (예: `"2026-07-14"`) | 수집 종료 상한 |
| `type` | `"auto"` | 품질·필터 호환 (권장) |
| `numResults` | `8`~`10` | 토픽당 |
| `enableSummary` | `true` | 전체 본문 대신 **깔끔한 요약**만 확보 |
| `summaryQuery` | `"EV/battery industry impact and key facts"` | 요약 초점 |
| `textMaxCharacters` | `250` | **전체 본문 반환 차단** |
| `excludeDomains` | `sources.py`의 `BLOCKLIST` | 알려진 콘텐츠팜 하드 차단 |

> ⚠️ **`textMaxCharacters`를 반드시 넣는다.** 생략하면 고급검색이 기사 **전체 본문**을
> 통째로 반환해(건당 최대 ~17,000자) Step 2 토큰이 몇 배로 튄다. 단, `1`처럼 과하게 낮추면
> 하이라이트/요약까지 깨지므로 `250`을 권장한다.

토픽 쿼리 예시 (날짜는 파라미터로 거르므로 쿼리에 날짜를 넣지 않아도 된다):

| 검색 토픽 | 예시 쿼리 |
|---|---|
| EV 배터리 기술 | `"EV battery electric vehicle battery technology news"` |
| K-배터리 / 경쟁사 | `"SK On CATL LG Energy Solution Samsung SDI battery news"` |
| 완성차 EV 동향 | `"Tesla BYD Hyundai Ford GM electric vehicle supply chain news"` |
| 정책 / 소재 / ESS | `"lithium nickel cobalt IRA energy storage ESS grid battery policy news"` |

### 2-B. 완화 사다리 (8건 미달 시 순서대로)

날짜+출처 필터 탓에 뉴스가 적은 날은 8건이 안 될 수 있다. 아래 순서로 완화한다:

1. `numResults`를 `15`~`20`으로 올려 재검색
2. `startPublishedDate`를 하루 더 앞으로 확대 (−2일)
3. `excludeDomains`(BLOCKLIST)만 유지한 채 토픽 쿼리를 다양화
4. 그래도 부족하면 **Naver 폴백(2-C)**

### 2-C. Naver Search MCP 폴백 (Exa 실패 시)

`mcp__PlayMCP__NaverSearch-search_news` 툴 사용.  
**반드시 `originallink` 필드를 URL로 사용한다** (link는 네이버 리다이렉트 주소).
Naver는 서버측 날짜 필터가 없으므로, 이 경로로 받은 기사는 2-D에서 날짜를 반드시 재확인한다.

### 2-D. 날짜 재검증 (얇은 안전망)

Exa 서버 날짜는 크롤링 추정값이라 경계 오배치·누락이 있을 수 있다.
받아온 각 기사의 `publishedDate`를 KST로 변환하여 **수집 범위 밖이면 제외**한다.

```
publishedAt(UTC) → KST 변환 → 전날 09:00 KST ≤ 기사 시각 < 오늘 09:00 KST
```

> 서버 필터가 1차, 이 재검증이 2차 안전망이다. **서버 필터를 믿고 이 단계를 생략하지 않는다.**

### 2-E. 출처 신뢰도 태깅

`daily_briefing/sources.py`의 목록을 기준으로 각 기사에 **`source_tier`**를 부여한다.
`classify_domain(url)` 결과 → `"TIER1"` / `"TIER2"` / `"UNKNOWN"`
(BLOCKLIST 도메인은 2-A에서 이미 제외됨; 폴백으로 유입 시 여기서 **하드 제외**).

- `source_tier`는 impact_score에 **약한 가중치**로만 반영한다: `UNKNOWN`은 −1 정도 감점,
  점수 산정 자체는 여전히 모델 판단으로 한다.
- 목록에 없는 매체라고 무조건 저신뢰는 아니다 — 내용으로 판단하되,
  **인사이트 선정(Step 4)에서만 출처를 엄격히 본다.**

최종 수집 기사는 **최대 15건**.

---

## Step 3 — 기사 분류 & 점수화

필터링을 통과한 각 기사에 아래 두 항목을 부여한다.

### 카테고리 (6개 중 하나)

| 카테고리 | 해당 내용 |
|---|---|
| `EV Maker` | 완성차 업체의 EV 판매·전략·신모델 |
| `EV 배터리 기술/산업` | 배터리 화학·셀 기술·제조 혁신·연구 결과 |
| `SK온/배터리 경쟁사` | SK온·CATL·LG에너지솔루션·삼성SDI·파나소닉 등 직접 관련 |
| `에너지 정책/규제` | 각국 EV·배터리 보조금·세제·안전 표준·IRA·FEOC |
| `배터리 광물/공급망` | 리튬·니켈·코발트·흑연·희토류 채굴·정제·공급망 |
| `ESS/에너지저장` | 유틸리티 ESS·AI 데이터센터 전력·그리드 저장 |

### impact_score (1~10)

아래 세 요소를 종합해 점수를 매긴다:

- **산업 전반 영향력** — 시장 규모·파급력·장기 구조 변화 여부
- **SK온 직접 관련성** — SK온의 경쟁·협력·규제 환경에 직접 영향
- **시장/정책 파급력** — 정책 결정·투자 규모·글로벌 트렌드 설정 여부

| 점수 범위 | 의미 |
|---|---|
| 8~10 | 산업 판도를 바꾸는 빅 이벤트 |
| 5~7 | 주목할 만한 중요 동향 |
| 1~4 | 참고 수준의 일반 기사 |

---

## Step 3.5 — 직전 인사이트 확인 (중복 방지)

인사이트(Step 4)를 고르기 전에 **최근 발송분과 같은 기사를 또 뽑지 않도록** 직전 이력을 확인한다.

### 3.5-A. Gmail 발송 이력 조회

Gmail MCP로 최근 발송 메일을 조회한다:

- `mcp__Gmail__search_threads` 쿼리: `subject:"[AI Morning Brief]" newer_than:4d`
- 최근 1~2건 스레드를 `mcp__Gmail__get_thread`로 열어 **인사이트 헤더 박스의 기사 제목/URL**을 추출한다.

각 직전 인사이트에 대해 **정규화된 스토리 키(`topic_key`)**를 뽑는다.
`topic_key`는 URL이 아니라 **사건 단위**로 잡는다 (예: `"SK온 배터리 결함 리콜"`).
→ 다른 매체가 같은 사건을 보도해도 같은 `topic_key`로 묶인다.

### 3.5-B. 폴백

Gmail 조회가 실패하면(커넥터 미연결·인증 만료 등) **중복 확인만 건너뛰고** 나머지는 정상 진행한다.
이 경우 "직전 이력 미확인" 상태임을 최종 보고에 명시한다.

---

## Step 4 — 인사이트 작성

### 인사이트 기사 선정 규칙

1. **후보 정렬:** 수집 기사를 `impact_score` 내림차순으로 본다.
2. **출처 교차검증:** 인사이트로 뽑는 기사는 반드시 **TIER1/TIER2**이면서
   **독립된 2개 이상 출처가 같은 사건을 보도**한 건이어야 한다.
   콘텐츠팜·단독 미확인 보도는 인사이트로 불가하다 (기사 테이블에는 실을 수 있음).
3. **중복 로테이션:** 최고 impact 기사의 `topic_key`가 **Step 3.5의 직전 인사이트와 같으면**,
   그다음으로 impact 높은 **다른 `topic_key` 기사**를 인사이트로 선정한다.
   - 예외: 같은 스토리라도 **중대한 신규 전개**가 있으면 허용하되, 반드시
     "후속/새 각도"로 프레이밍한다 (예: 리콜 → 배터리팩 교체 비용·주가 반응 등).
4. **정보 손실 없음:** 로테이션하는 건 '인사이트 1건'뿐이다.
   그 대형 이슈는 기사 테이블에 계속 실어도 된다.

위 규칙으로 선정한 기사 1건에 대해 **한국어 인사이트를 600~700단어**로 작성한다.

### 필수 4개 섹션 (소제목 형식 엄수)

```
## 배경
왜 이 뉴스가 나왔는가 — 시장 배경, 정책 맥락, 직전 사건 흐름

## 핵심 내용
무슨 일이 일어났는가 — 수치·날짜·당사자·주요 발언 등 팩트 중심

## 산업 영향
EV/배터리 산업 전반에 어떤 의미인가 — 구조적 변화, 경쟁 지형, 기술 표준 등

## SK온 관점에서의 시사점
SK온에게 기회인가 위협인가 — 구체적 행동 방향 포함
```

### 서식 규칙

- 소제목은 반드시 `## 배경`, `## 핵심 내용`, `## 산업 영향`, `## SK온 관점에서의 시사점` 형식 사용
- 수치·키워드·핵심 판단은 `**굵게**` 마크다운 형식으로 강조
- 사실에 기반한 서술, 추측은 "~로 보인다", "~가 예상된다" 등으로 구분

---

## Step 5 — JSON 파일 작성

`/tmp/briefing_input.json`을 아래 스키마로 작성한다.

```json
{
  "date_str": "YYYY-MM-DD",
  "articles": [
    {
      "id": 1,
      "title": "기사 제목",
      "url": "https://원본-직접-링크",
      "publishedAt": "2026-06-30T08:00:00Z",
      "category": "위 6개 중 하나",
      "summary": "요약 1줄\n요약 2줄\n요약 3줄",
      "impact_score": 8,
      "source_tier": "TIER1",
      "topic_key": "SK온 배터리 결함 리콜"
    }
  ],
  "insight": "## 배경\n\n...\n\n## 핵심 내용\n\n...\n\n## 산업 영향\n\n...\n\n## SK온 관점에서의 시사점\n\n..."
}
```

**필드 설명:**

| 필드 | 설명 |
|---|---|
| `date_str` | 오늘 날짜 (`YYYY-MM-DD`) |
| `articles` | 필터링·점수화된 기사 목록 (최대 15건) |
| `id` | 1부터 순번 |
| `title` | 원문 제목 그대로 |
| `url` | 원본 기사 직접 링크 (리다이렉트 URL 사용 금지) |
| `publishedAt` | ISO 8601 형식 (Z 또는 +09:00 등) |
| `category` | 위 6개 카테고리 중 하나 |
| `summary` | 핵심 내용 3줄, `\n`으로 구분 |
| `impact_score` | 1~10 정수 |
| `source_tier` | `TIER1`/`TIER2`/`UNKNOWN` (`sources.py` `classify_domain` 기준) |
| `topic_key` | 사건 단위 정규화 키 (중복 판단용) |
| `insight` | Step 4에서 작성한 한국어 인사이트 전문 |

> `articles`는 `impact_score` 내림차순으로 정렬하지 않아도 된다. `run.py`가 자동 정렬한다.
> `source_tier`·`topic_key`는 내부 판단용 필드로, 이메일 렌더링에는 사용되지 않는다(`run.py`가 무시).

---

## Step 6 — 이메일 발송 (run.py 실행)

환경 변수 3개(`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`)가 모두 설정된 경우에만 수행한다.

```bash
cd daily_briefing && python run.py --input /tmp/briefing_input.json
```

> **`--draft` 플래그를 절대 붙이지 않는다.** `--draft`는 테스트 전용이며 실제 발송을 막는다.

### 성공 확인

콘솔에 아래와 같이 출력되면 발송 성공:

```
[OK] 제목: [AI Morning Brief] 2026-07-01 배터리 (EV/ESS) 핵심 동향
     수신자: ['jupiter@sk.com', ...]
     HTML → /tmp/email_output.json
[SENT] Gmail API message id: <message_id>
```

`[SENT] Gmail API message id: ...`가 출력되면 Step 7은 **건너뛴다**.

### 출력 파일

`/tmp/email_output.json` — 발송 성공 여부와 무관하게 항상 생성됨. 아래 구조:

```json
{
  "to": ["jupiter@sk.com", ...],
  "subject": "[AI Morning Brief] YYYY-MM-DD 배터리 (EV/ESS) 핵심 동향",
  "htmlBody": "<html>...</html>"
}
```

---

## Step 7 — 발송 실패 시 폴백 (Gmail 초안 생성)

Step 6이 실패한 경우(환경 변수 누락, 토큰 만료, `[SENT]` 미출력, 예외 발생)에만 수행한다.

`/tmp/email_output.json`의 값을 그대로 사용해 Gmail MCP `create_draft`를 호출한다:

```
to      : email_output.json의 to 값
subject : email_output.json의 subject 값
htmlBody: email_output.json의 htmlBody 값  ← 수정 금지
```

초안 생성 후, "자동 발송 실패로 초안으로 대체했음 — 수동 확인 및 발송 필요"를 명확히 알린다.

---

## 이메일 출력 형식 (참고)

`run.py` → `send_email.py`의 `build_email()` 함수가 HTML 이메일을 생성한다.

| 섹션 | 내용 |
|---|---|
| 헤더 | `[AI Morning Brief] YYYY-MM-DD` 제목 |
| 기사 테이블 | 카테고리 순 → impact_score 내림차순 정렬; 중요도는 색상 동그라미(빨강 ≥8, 파랑 ≥5, 회색 나머지) |
| 인사이트 | `## 소제목` → 굵은 파란 세로선 박스; `**text**` → `<strong>` |
| 푸터 | "Claude AI 자동 생성" + 기준 날짜 |

---

## 코드베이스 파일 구조 (참고)

```
daily_briefing/
├── config.py         # 수신자, 카테고리, 모델명 등 상수
├── sources.py        # 출처 신뢰도 목록 (TIER1/2·BLOCKLIST) + classify_domain()
├── fetch_news.py     # get_kst_window() — 시간 범위 계산
├── run.py            # 진입점: JSON 읽기 → HTML 빌드 → Gmail API 발송
├── send_email.py     # build_email() — HTML 이메일 렌더링
├── gmail_sender.py   # send_email_via_api() — Gmail REST API 호출
├── render.py         # (보조) 렌더링 유틸
├── insight.py        # (보조) 인사이트 생성 유틸
└── summarize.py      # (보조) 요약 유틸
```

---

## 체크리스트

루틴 완료 전 아래 항목을 확인한다:

- [ ] `daily-news-briefing-v1` 브랜치 체크아웃 완료
- [ ] 수집 시간 범위(전날 KST 09:00 ~ 오늘 KST 09:00) 정확히 계산
- [ ] Exa 고급검색에 `startPublishedDate`/`endPublishedDate` + `textMaxCharacters` 적용
- [ ] 날짜 재검증 통과 기사 **8건 이상** 확보 (미달 시 완화 사다리)
- [ ] 각 기사에 카테고리 · impact_score · `source_tier` 부여
- [ ] Step 3.5 직전 인사이트 확인 (또는 실패 시 "미확인" 명시)
- [ ] 인사이트 기사: TIER1/2 + 2개 이상 출처 교차검증, 직전과 `topic_key` 중복 아님
- [ ] 인사이트 4개 섹션 모두 포함, 600~700단어
- [ ] `/tmp/briefing_input.json` 스키마 오류 없음
- [ ] `run.py` 실행 시 `--draft` 플래그 미사용
- [ ] `[SENT] Gmail API message id: ...` 확인 (또는 폴백 초안 생성)
