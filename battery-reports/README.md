# battery-reports — K-배터리 증권사 리포트 DB

2차전지 산업 및 3사(LG에너지솔루션·삼성SDI·SK온) 증권사 리포트를 **여러 프로젝트에서 재사용**하기 위한 저장소.

## 핵심 원리

> **원문(MD)** 과 **구조화 데이터(인덱스)** 를 분리한다.

- `reports/` 의 MD = 사람과 Claude가 **읽는** 전체 원문/구조화 요약 (맥락)
- `index/` 의 CSV·JSONL = **필터·집계·차트**용 정형 데이터

각 리포트 MD는 상단 **YAML frontmatter(구조화 메타데이터)** + 하단 **표준 본문**으로 구성된다.
frontmatter 필드가 곧 DB 컬럼이다. 기본 양식은 [`schema/template.md`](schema/template.md), ESS 시장/경쟁사 확장 규칙은 [`schema/ESS_INTELLIGENCE.md`](schema/ESS_INTELLIGENCE.md)를 따른다.

## 폴더 구조

```
battery-reports/
├── inbox/                       # 원본 PDF
├── reports/YYYY/                # 표준 MD
├── index/
│   ├── reports.jsonl
│   ├── estimates.csv
│   ├── stances.csv
│   ├── demand_forecasts.csv     # 기존/웹사이트 하위호환
│   ├── demand_forecasts_v2.csv  # ESS Region×Application×Source 확장 인덱스
│   └── company_metrics.csv      # K-battery + 경쟁사 ESS intelligence
├── schema/
│   ├── template.md
│   ├── NORMALIZATION.md
│   └── ESS_INTELLIGENCE.md
├── tools/
│   ├── build_indexes.py         # 기존/웹사이트 인덱스
│   ├── build_ess_indexes.py     # ESS 확장 인덱스
│   └── build_all.py             # 신규 인제스트 권장 실행점
└── projects/
    └── ess_market_intelligence/ # 15개 기업리포트 backfill 등 분석 산출물
```

## 사용법 (비개발자)

### 1) 리포트 넣기 (인제스트)
1. PDF를 `inbox/` 에 넣는다.
2. Claude에게 **"inbox의 리포트를 인제스트해줘"**라고 요청한다.
3. 인제스트는 `schema/template.md` 및 `schema/ESS_INTELLIGENCE.md`를 모두 따른다.
4. 신규 인제스트 완료 후 권장 빌드:

```bash
python3 tools/build_all.py
```

검증만 할 때:

```bash
python3 tools/build_all.py --check
```

`build_all.py`는 기존 웹사이트 인덱스를 먼저 만들고, 이어서 ESS 확장 인덱스를 생성한다. 기존 `demand_forecasts.csv`는 깨지지 않는다.

### 2) ESS 데이터 인제스트 원칙

기업/산업 리포트 구분 없이 **시장 자체의 정량 전망**이면 `demand_forecasts`에 넣는다.

- 시장 수요/설치량/출하량/CAGR/침투율 → `demand_forecasts`
- LGES·삼성SDI·SK온·CATL·BYD 등 특정 회사의 CAPA·출하량·수주잔고·시장점유율 → `company_metrics`
- 숫자 없는 산업 방향성 → `industry_views` / `themes`

ESS는 반드시 **Region × Application × Metric × FY**를 기준으로 구조화한다.

Application은 증권사마다 정의가 다르므로 원문과 표준을 함께 보존한다.

- `application_raw`: 원문 그대로
- `application_std`: `Total | Grid | Data Center | C&I | Residential | Other`
- `application_detail`: 예: `BESS | UPS | BBU | Utility | Solar-linked`

Region도 `region_raw`와 `region_std`를 함께 둔다. **미국(US)과 북미(North America)는 자동으로 합치지 않는다.**

또한 같은 숫자가 GGII/BNEF/SNE 등 외부기관 전망을 여러 증권사가 재인용한 것인지 구분하기 위해 `source_org`와 `source_type`을 기록한다.

### 3) 분석하기
Claude에게 원하는 분석을 요청하면 `index/` 를 조회해 `projects/<이름>/` 에 결과를 쓴다. 예:

- "삼성SDI 목표주가를 증권사별 시계열로 보여줘" → `estimates.csv`
- "LFP·46파이·ESS·북미CAPEX·수율에 대한 3사 비교표" → `stances.csv`
- "미국 Data Center ESS 2030 전망을 증권사/원출처별 비교" → `demand_forecasts_v2.csv`
- "미국 Grid ESS에서 LGES/SDI/CATL/BYD 경쟁구도" → `company_metrics.csv`

## ESS 15개 기업리포트 backfill

ESS 시장 데이터 밀도가 높은 기업리포트 15건은 `projects/ess_market_intelligence/backfill_15.json`에 1차 구조화했다.

현재 환경에서는 GitHub의 원본 PDF 바이너리를 직접 렌더링하지 못했으므로 기존 인제스트 시 생성된 MD와 페이지 추적값을 사용했다. 따라서 해당 행은 `verification_status=md_backfill`로 표시한다. 원본 PDF를 직접 열 수 있는 환경에서 재검증하면 `pdf_verified`로 승격한다.

## 시작 규모 권장

새 스키마는 소규모 실제 분석으로 검증한 뒤 확대한다. 과거 PDF 전량을 무차별 재파싱하기보다 **index discovery → MD screening → targeted PDF review** 방식으로 backfill한다.

## 성장 경로

연 200~300건 수준이면 MD + CSV/JSONL 방식으로 수 년간 충분하다. 규모가 크게 증가하거나 실시간 다중 조회가 필요해지면 `index/`만 SQLite로 승격한다.
