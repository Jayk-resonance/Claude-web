# battery-reports — K-배터리 증권사 리포트 DB

2차전지 산업 및 3사(LG에너지솔루션·삼성SDI·SK온) 증권사 리포트를 **여러 프로젝트에서 재사용**하기 위한 저장소.

## 핵심 원리

> **원문(MD)** 과 **구조화 데이터(인덱스)** 를 분리한다.

- `reports/` 의 MD = 사람과 Claude가 **읽는** 전체 원문 (맥락)
- `index/` 의 CSV·JSONL = **필터·집계·차트**용 정형 데이터 (점도표, 컨센서스, 비교표의 연료)

각 리포트 MD는 상단 **YAML frontmatter(구조화 메타데이터)** + 하단 **표준 본문**으로 구성된다.
frontmatter 필드가 곧 "DB 컬럼"이다. 표준 양식은 [`schema/template.md`](schema/template.md).

## 폴더 구조

```
battery-reports/
├── inbox/              # ← 원본 PDF를 여기 넣는다 (사용자의 유일한 수작업)
├── reports/YYYY/       # 표준 MD. 파일명 = YYYY-MM-DD_증권사_커버리지.md
├── index/
│   ├── reports.jsonl   # 리포트 1건 = 1행 (frontmatter 집약, 자동 갱신)
│   ├── estimates.csv   # (리포트×회사×세그먼트×지표×기간) 추정치
│   └── stances.csv     # (리포트×이슈×회사) 이슈별 스탠스
├── schema/template.md  # 표준 양식 (DB 스키마). 매 인제스트마다 강제.
└── projects/           # 분석 결과물. 원천(reports·index)은 절대 수정하지 않는다.
```

## 사용법 (비개발자)

### 1) 리포트 넣기 (인제스트)
1. PDF를 `inbox/` 에 넣는다.
2. Claude에게: **"inbox의 리포트를 인제스트해줘"**
   → PDF를 `schema/template.md` 형식의 MD로 변환해 `reports/YYYY/` 에 저장
   → `index/` 3개 파일에 **행 추가(append)만** 한다. 전체 재빌드 없음 → 월 20건·분기 60~80건 증분에 적합.
   → 원본 PDF 경로와 페이지를 남겨 **모든 숫자를 역추적** 가능하게 한다.

### 2) 분석하기
Claude에게 원하는 분석을 요청하면 `index/` 를 조회해 `projects/<이름>/` 에 결과를 쓴다. 예:
- "삼성SDI 목표주가를 증권사별 시계열로 보여줘" (→ estimates.csv)
- "LFP·46파이·ESS·북미CAPEX·수율에 대한 3사 비교표를 만들어줘" (→ stances.csv)
- "2026E 3사 합산 영업이익 추정치로 FOMC식 점도표를 그려줘" (→ estimates.csv)
- "미래에셋의 SK온 View가 시간에 따라 어떻게 바뀌었는지 추적해줘"

## 시작 규모 권장
100개를 한 번에 하지 말 것. **한 분기(약 20개)로 스키마를 먼저 검증** → 분석 2~3개를 실제로 돌려
스키마가 그 분석을 지탱하는지 확인 → 전량 확장. (과잉설계 방지)

## 성장 경로
연 200~300건 수준이면 이 방식(MD + CSV/JSONL)으로 수 년간 충분하다.
정말 커지거나 실시간 다중 조회가 필요해지면 그때 `index/` 만 SQLite(파일 1개)로 승격하면 된다.
지금은 불필요하다.
