---
# 리포트 표준 메타데이터 (= DB 컬럼). 매 인제스트마다 이 형식을 강제한다.
report_id: 2026-01-15_미래에셋_LGES
date: 2026-01-15
house: 미래에셋
analyst: null
coverage: LGES                          # LGES | 삼성SDI | SK온 | 산업
report_type: 기업                       # 기업 | 산업
opinion: 매수                            # 매수 | 중립 | 매도 | null
target_price: 450000
prev_target_price: 420000

# 회사/세그먼트 손익 추정치. 금액 중심 회사 전망은 여기 저장.
estimates:
  - {company: LGES, segment: 전사, segment_std: 전사, fy: 2026, period: FY, metric: 영업이익, value: 993, unit: 십억원, ampc_basis: incl, page: 3}
  - {company: LGES, segment: 전사, segment_std: 전사, fy: 2026, period: FY, metric: AMPC, value: 1425, unit: 십억원, ampc_basis: na, page: 3}
  - {company: LGES, segment: ESS, segment_std: ESS, fy: 2026, period: 2Q, metric: 매출, value: 2062, unit: 십억원, ampc_basis: excl, page: 3}

stances:
  - {issue: ESS, company: LGES, stance_score: 6, summary: "미국 ESS 수요 확대 수혜", page: 2}

key_issues: [ESS, LFP, 북미CAPEX]

# 숫자 없는 시장 방향성/논거. 기업/산업 리포트 모두 허용.
industry_views:
  - {scope: 북미ESS, fy: 2026, metric: 수요, value: null, unit: GWh, direction: 2, summary: "AI 데이터센터발 수요 급증", page: 2}

# 정량 시장 전망. 기업/산업 리포트 구분 없이 수집한다.
# 기존 region/application 필드는 하위호환용. ESS 상세 분석은 raw/std/detail을 추가한다.
demand_forecasts:
  - {region: 북미, application: ESS, region_raw: 미국, region_std: US, application_raw: "AI Data Center ESS", application_std: "Data Center", application_detail: BESS, metric: 수요량, forecast_type: demand, fy: 2030, value: 160, value_low: null, value_high: null, value_prev: null, unit: GWh, basis: "미국 AIDC향 ESS 시장", source_org: 미래에셋, source_name: null, source_type: broker_estimate, page: 2, verification_status: pdf_verified}

# ESS 회사/경쟁사 물리량·시장지위. 손익 금액은 estimates에 두고 CAPA/출하/수주/M/S 중심으로 사용.
company_metrics:
  - {company: LGES, entity_type: company, company_group: K-battery, region_raw: 미국, region_std: US, application_raw: "ESS 전체", application_std: Total, application_detail: null, metric: capacity, fy: 2026, value: 50, value_low: null, value_high: null, unit: GWh, basis: "미국 ESS 생산능력", source_org: 미래에셋, source_type: broker_estimate, page: 2, verification_status: pdf_verified}
  - {company: CATL, entity_type: company, company_group: China, region_raw: 미국, region_std: US, application_raw: "Utility-Grid ESS", application_std: Grid, application_detail: Utility, metric: market_share, fy: 2027, value: 40, value_low: null, value_high: null, unit: "%", basis: "미국 Utility/Grid ESS", source_org: 미래에셋, source_type: broker_estimate, page: 5, verification_status: pdf_verified}

top_picks: []
source_pdf: inbox/미래에셋_20260115.pdf
---

## 핵심 요약
<!-- 3~5줄. -->

## 투자의견·목표주가 (도출 근거)
<!-- 밸류에이션 방법, 멀티플, 변경 사유. -->

## 사업부문별 손익
<!-- frontmatter estimates와 일치. -->

## 이슈별 코멘트
<!-- LFP / 46파이 / ESS / 북미CAPEX / 수율 등. -->

## 리스크 요인

## 원문 인용
<!-- 핵심 주장은 원문 그대로 보존하고 (p.N) 페이지를 표기. -->

---

# 부록. 인제스트 입력 형식 — `.staging/<report_id>.json`

MD는 직접 작성하지 않는다. 인제스트는 staging JSON을 만들고 빌더가 MD/인덱스를 생성한다.

```jsonc
{
  "report_id": "2026-01-15_미래에셋_LGES",
  "date": "2026-01-15",
  "house": "미래에셋",
  "analyst": null,
  "coverage": "LGES",
  "report_type": "기업",
  "opinion": "매수",
  "target_price": 450000,
  "prev_target_price": 420000,
  "key_issues": ["ESS", "북미CAPEX"],
  "top_picks": [],
  "estimates": [],
  "stances": [],
  "industry_views": [],
  "demand_forecasts": [
    {
      "region": "북미",
      "application": "ESS",
      "region_raw": "미국",
      "region_std": "US",
      "application_raw": "AIDC향 ESS",
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
      "source_org": "미래에셋",
      "source_name": null,
      "source_type": "broker_estimate",
      "page": 5,
      "verification_status": "pdf_verified"
    }
  ],
  "company_metrics": [
    {
      "company": "CATL",
      "entity_type": "company",
      "company_group": "China",
      "region_raw": "미국",
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
      "source_org": "미래에셋",
      "source_type": "broker_estimate",
      "page": 7,
      "verification_status": "pdf_verified"
    }
  ],
  "themes": [],
  "body": {
    "summary": "...",
    "valuation": "...",
    "segment_pl": "...",
    "issue_comments": "...",
    "risks": "...",
    "quotes": "..."
  }
}
```

## ESS 분류 원칙

상세 규칙은 `schema/ESS_INTELLIGENCE.md`를 따른다.

- 시장 전체/서브시장 정량 전망 → `demand_forecasts`
- LGES·삼성SDI·SK온·CATL·BYD 등 특정 회사/그룹의 CAPA·출하량·수주잔고·시장점유율 → `company_metrics`
- 숫자 없는 시장 방향성 → `industry_views` / `themes`
- `region_raw`와 `region_std`를 모두 보존. 미국과 북미를 임의 통합하지 않는다.
- `application_raw`와 `application_std/detail`을 모두 보존.
- `application_std`: `Total | Grid | Data Center | C&I | Residential | Other`
- Data Center의 BESS/UPS/BBU는 `application_detail`로 구분한다.
- 같은 외부기관 전망 재인용을 식별하도록 `source_org`와 `source_type`을 기록한다.
- 범위 전망은 `value=null`, `value_low`, `value_high`를 사용한다.
- 시장 `demand/shipment/installation/capacity`를 동일 GWh라고 합치지 않는다.
- 기존 MD에서 backfill한 값은 `md_backfill`; 원본 PDF를 직접 확인한 값은 `pdf_verified`.

## body 키 → MD 섹션

| body 키 | MD 섹션 |
|---|---|
| `summary` | `## 핵심 요약` |
| `valuation` | `## 투자의견·목표주가 (도출 근거)` |
| `segment_pl` | `## 사업부문별 손익` |
| `issue_comments` | `## 이슈별 코멘트` |
| `risks` | `## 리스크 요인` |
| `quotes` | `## 원문 인용` |

## 빌드/검증

신규 인제스트는 다음을 권장한다.

```bash
python3 tools/build_all.py --check
python3 tools/build_all.py
```

`build_all.py`는 기존 웹사이트용 인덱스와 ESS 확장 인덱스를 모두 생성한다.
