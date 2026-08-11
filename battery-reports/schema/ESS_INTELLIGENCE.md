# ESS Market & Company Intelligence 스키마

ESS 데이터를 실제 리서치에 재사용하기 위한 확장 규칙. 기존 `estimates.csv`, `demand_forecasts.csv`, `industry_views.csv`는 유지하면서 ESS 시장/회사/경쟁사 데이터를 더 세밀하게 구조화한다.

## 1. 핵심 원칙

1. **Market와 Company를 절대 섞지 않는다.**
   - 시장 전체/서브시장 수요·설치량·출하량·성장률·침투율 → `demand_forecasts`
   - LGES·삼성SDI·SK온·CATL·BYD 등 특정 회사/그룹의 CAPA·출하량·수주잔고·점유율 등 → `company_metrics`
2. **원문 분류와 표준 분류를 동시에 보존한다.** 증권사별 분류 체계가 달라도 원문을 잃지 않는다.
3. **Region × Application × Metric × FY**가 기본 분석 키다.
4. 숫자의 1차 출처를 분리한다. 증권사 자체 추정인지 GGII/BNEF/SNE 등 외부기관 인용인지 반드시 기록한다.
5. PDF/원문 페이지까지 역추적 가능해야 한다. 확신이 낮으면 억지 표준화하지 않고 raw 값을 보존한다.

## 2. Region

### 저장 필드
- `region_raw`: 원문 그대로. 예: `US`, `North America`, `미국`
- `region_std`: 분석용 표준값

### region_std 권장값
`Global | North America | US | Europe | China | Korea | APAC | Other`

주의: **US와 North America를 자동 통합하지 않는다.** 원문이 North America면 `North America`, 미국이면 `US`로 둔다.

## 3. ESS Application

증권사마다 `AIDC`, `Data Center`, `Utility`, `Grid`, `VRE`, `Residential`, `UPS/BBU` 등 표현이 다르므로 raw/std/detail 3단계를 사용한다.

### 저장 필드
- `application_raw`: 원문 표현 그대로
- `application_std`: 상위 분석용 분류
- `application_detail`: 하위 세부 분류

### application_std
- `Total`: Application 구분 없는 전체 ESS
- `Grid`: Utility/Grid-scale/VRE/재생에너지 연계
- `Data Center`: AI Data Center 및 데이터센터 전력 인프라
- `C&I`: 상업·산업용/일반 BTM
- `Residential`: 주거용
- `Other`: 그 외

### application_detail 예시
- Data Center → `BESS`, `UPS`, `BBU`, `UPS/BBU`, `On-site BESS`
- Grid → `Utility`, `Grid-scale`, `Solar-linked`, `Renewable-linked`, `VRE-linked`
- Residential → `Home ESS`

분류가 애매하면 `application_std=Other` 또는 `Total`로 두고 `application_raw`를 보존한다. **UPS/BBU를 일반 Grid BESS와 합치지 않는다.**

## 4. demand_forecasts 확장 필드

기존 필드와의 하위호환을 유지한다. `application`은 기존 대분류(EV|ESS|합계)를 유지하며, ESS 세부 분류는 아래 필드를 추가한다.

```jsonc
{
  "region": "북미",                 // 기존 필드, 하위호환
  "application": "ESS",            // 기존 필드, 하위호환
  "region_raw": "US",
  "region_std": "US",
  "application_raw": "AI Data Center ESS",
  "application_std": "Data Center",
  "application_detail": "BESS",
  "metric": "수요량",
  "forecast_type": "demand",
  "fy": 2030,
  "value": 160,
  "value_low": null,
  "value_high": null,
  "value_prev": null,
  "unit": "GWh",
  "basis": "미국 AIDC향 ESS 수요",
  "source_org": "증권사명 또는 GGII/BNEF/SNE 등",
  "source_name": "표/차트/자료명 또는 null",
  "source_type": "broker_estimate",
  "page": 5,
  "verification_status": "pdf_verified"
}
```

### forecast_type 통제어휘
`demand | shipment | installation | capacity | growth_rate | penetration | market_share | actual | other`

- 같은 GWh라도 `demand`, `shipment`, `installation`, `capacity`를 섞지 않는다.
- 범위 전망(예: 150~180GWh)은 `value=null`, `value_low=150`, `value_high=180`으로 저장한다.
- `value` 하나만 있는 기존 행은 그대로 허용한다.

### source_type
- `broker_estimate`: 증권사 자체 추정
- `external_republication`: 외부기관 전망을 증권사가 재인용
- `market_consensus`: 시장 컨센서스 범위
- `reported_observation`: 발표된 실적/설치량 등 관측치
- `company_guidance`: 회사 가이던스
- `other`

### verification_status
- `pdf_verified`: 원본 PDF의 표/본문/페이지를 직접 확인
- `md_backfill`: 기존 PDF 인제스트에서 생성된 MD/페이지 정보를 이용한 backfill. 향후 원본 PDF 재검증 가능
- `needs_pdf_review`: 수치/범위/정의가 애매해 PDF 재확인 필요

## 5. company_metrics

ESS 경쟁구도와 회사 운영지표 전용 테이블. `estimates.csv`의 손익추정치와 중복시키기보다 **물리량·시장지위·수주·CAPA 중심**으로 사용한다.

```jsonc
{
  "company": "CATL",
  "entity_type": "company",
  "company_group": "China",
  "region_raw": "US",
  "region_std": "US",
  "application_raw": "Utility-Grid ESS",
  "application_std": "Grid",
  "application_detail": "Utility",
  "metric": "market_share",
  "fy": 2027,
  "value": 40,
  "value_low": null,
  "value_high": null,
  "unit": "%",
  "basis": "미국 Utility/Grid ESS",
  "source_org": "증권사명/외부기관",
  "source_type": "broker_estimate",
  "page": 7,
  "verification_status": "pdf_verified"
}
```

### entity_type
- `company`: LGES, 삼성SDI, SK온, CATL, BYD, EVE, CALB, REPT 등 개별 회사
- `group`: 중국 셀사, K-battery, 일본 업체 등 집단 수치

### company_group 권장값
`K-battery | China | Japan | Europe-US | Other`

### metric 권장값
`capacity | shipment | backlog | order_target | market_share | production | utilization | ampc_volume | other`

금액 중심 손익 추정은 원칙적으로 `estimates.csv`에 둔다. 시장/경쟁 분석에 직접 필요한 회사 ESS 물리량만 `company_metrics`로 중복 허용한다.

## 6. 중복 전망 방지

같은 외부기관 숫자가 여러 증권사 기업리포트에 반복될 수 있다. 예를 들어 GGII 2030 AIDC ESS 272GWh가 iM의 LGES/삼성SDI 리포트에 반복되면 **독립 전망 2개로 세지 않는다.**

중복 식별 키 권장:
`source_org + region_std + application_std + application_detail + forecast_type + fy + value/value_low/value_high + unit`

하우스별 View 분석에서는 report_id를 유지하되, 시장 컨센서스 산출 시 동일 `source_org` 중복을 제거한다.

## 7. 인제스트 규칙

새 PDF 인제스트 시 다음 순서로 한 번에 수집한다.

1. 시장 전망 → `demand_forecasts`
2. 커버리지 회사의 ESS 물리/경쟁 데이터 → `company_metrics`
3. 경쟁사/국가그룹 ESS 데이터 → `company_metrics`
4. 숫자 없는 방향성 → `industry_views` / `themes`
5. 각 숫자에 `source_org`, `source_type`, `page`를 기록
6. `application_raw/std/detail`과 `region_raw/std`를 모두 기록
7. 확신이 없으면 `verification_status=needs_pdf_review`

## 8. 빌드

기존 `tools/build_indexes.py`는 웹사이트 하위호환 인덱스를 만든다. ESS 확장 인덱스는 이어서 실행한다.

```bash
python3 tools/build_indexes.py
python3 tools/build_ess_indexes.py
```

또는 신규 인제스트에서는 `python3 tools/build_all.py`를 권장한다.
