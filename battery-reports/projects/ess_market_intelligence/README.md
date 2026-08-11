# ESS Market Intelligence — 15개 기업리포트 backfill

## 범위

Index discovery → MD screening으로 선정한 기업리포트 15건을 대상으로 ESS 시장/회사/경쟁사 데이터를 구조화했다.

- 대상 리포트: 15건
- `demand_forecasts` backfill: 24행
- `company_metrics` backfill: 11행
- 원천: 기존 PDF 인제스트가 생성한 MD/frontmatter/페이지 추적값

현재 실행 환경에서는 GitHub `inbox/` PDF의 바이너리 본문을 렌더링하지 못해 원본 PDF를 시각적으로 재검증하지 못했다. 따라서 backfill 행은 기본적으로 `verification_status=md_backfill`이며, 향후 PDF 직접 접근이 가능한 환경에서 표/차트를 대조하면 `pdf_verified`로 승격한다.

## 데이터 구조

시장 데이터는 `Region × Application × Metric × FY`로 저장한다.

- Region: raw/std 동시 보존. US와 North America를 구분한다.
- Application: raw/std/detail 동시 보존.
  - Total
  - Grid
  - Data Center
  - C&I
  - Residential
  - Other
- Data Center 세부: BESS / UPS / BBU / UPS-BBU 등
- Metric: demand / shipment / installation / growth / penetration / market share 등을 분리한다.

회사/경쟁사 데이터는 `company_metrics`에 별도 저장한다.

- K-battery: LGES, 삼성SDI, SK온
- China: CATL, BYD 등 개별 회사 또는 `중국 셀사` 그룹
- CAPA, 출하량, 수주잔고, 시장점유율 등 물리/경쟁지표 중심
- 손익 금액은 기존 `estimates`가 원칙

## 주요 backfill 사례

- iM/삼성SDI: GGII AIDC ESS 출하량 2025 12GWh → 2027 61GWh → 2030 272GWh, AIDC 비중 5% → 31%
- LS/삼성SDI: 미국 AIDC ESS 수요 2026 9GWh → 2030 160GWh
- 삼성/LGES: 2027 북미 ESS 수요 135GWh, LGES 북미 CAPA 58GWh, 2027 M/S 43%
- LS/LGES: 2025 글로벌 ESS 550GWh, 2026 글로벌 이차전지 수요 내 ESS 비중 30%, 미국 ESS 18GWh
- iM/LGES·삼성SDI: 2030 미국 ESS 시장 컨센서스 150~180GWh를 범위값으로 저장
- LS/LGES: 미국 ESS 중국 셀사 M/S 50%+, Utility/Grid 70%대

## 파일

- `backfill_15.json`: 15개 리포트의 감사 가능한 backfill 원천
- `../../schema/ESS_INTELLIGENCE.md`: 표준 스키마/정규화 규칙
- `../../tools/build_ess_indexes.py`: staging + backfill을 ESS 확장 인덱스로 생성
- `../../tools/build_all.py`: 기존 인덱스 + ESS 확장 인덱스 통합 빌드

## 다음 검증 단계

PDF 직접 접근이 가능한 환경에서 `md_backfill` 행을 원본 페이지와 대조한다. 특히 다음을 우선 검증한다.

1. 수요/출하/설치/CAPA 정의
2. 미국 vs 북미 scope
3. AIDC BESS vs UPS/BBU scope
4. CAGR의 시작/종료 연도
5. `source_org`가 증권사 자체 추정인지 GGII/BNEF/SNE 등 외부기관 재인용인지
6. 범위값의 상·하단 및 단위
