# 정규화 규칙 (스키마 v2)

모든 인제스트·분석 프로젝트가 따라야 하는 표준. 원문 충실도(as-reported)를 유지하면서 교차 비교를 가능하게 하는 두 개의 정규화 축을 정의한다.

## 1. 사업부문 표준화 — `segment_std`

원칙: **각 리포트가 준 가장 세밀한 단위 그대로 저장**하고(원문 `segment` 보존), 위로 합산 가능한 계층에 매핑한다. 합본으로만 준 것을 쪼개지 않는다(숫자 창조 금지).

```
전사                      # 회사 전체 (SK이노베이션 연결 포함)
├─ 배터리합계              # 전지사업 전체 (삼성SDI '전지', SK온 '배터리')
│   ├─ 소형               # 원통형/소형전지(IT)
│   └─ 중대형             = EV + ESS
│       ├─ EV            # 자동차전지
│       └─ ESS
├─ 전자재료               # 삼성SDI만
└─ (AMPC는 부문이 아니라 metric으로 처리 — 아래 2절)
```

매핑표:
| 원문 부문 | segment_std |
|---|---|
| LGES 자동차, EV | EV |
| LGES/공통 ESS | ESS |
| LGES 중대형, 삼성SDI 중대형전지(EV,ESS), 2차전지(EV+ESS) | 중대형 |
| LGES 소형/원통형, 삼성SDI 소형전지(IT), 2차전지(IT) | 소형 |
| 삼성SDI 전지, SK온 배터리 | 배터리합계 |
| 삼성SDI 전자재료 | 전자재료 |
| SK이노베이션 연결전사, 각사 전사 | 전사 |
| 그 외 (윤활유, 석유개발 등 비배터리) | 기타 |

비교 규칙: 3사 교차 비교는 **공통으로 존재하는 가장 굵은 레벨**에서 한다.
- 배터리합계 레벨 → 3사 모두 가능 (LGES·SDI는 소형+중대형 합산)
- EV/ESS 분리 레벨 → 분리 공시한 증권사만 참여 (합본 리포트는 자동 제외, 억지 배분 금지)

## 2. AMPC 표준화 — `ampc_basis` + metric `AMPC`

문제: 증권사마다 (a) 부문 영업이익에 AMPC를 포함/제외, (b) LGES는 2026년부터 매출에도 AMPC 반영, (c) AMPC를 EV/ESS로 쪼개 공시하기도 함.

원칙: **AMPC는 항상 별도 행(metric=AMPC)으로 저장**하고, 모든 매출·영업이익 행에 `ampc_basis` 플래그를 붙인다.

| ampc_basis | 의미 |
|---|---|
| `excl` | 이 행의 값은 AMPC 제외 |
| `incl` | AMPC 포함 (같은 단위의 AMPC 행이 있으면 차감 가능) |
| `incl_unknown` | AMPC 포함이지만 금액 미공시 → 차감 불가, 비교 시 각주 경고 |
| `na` | 해당 없음 (AMPC 행 자체, 전자재료 등) |

파생 지표 (인덱스에 저장하지 않고 분석 시 도출):
```
영업이익_excl = ampc_basis=excl ? 값 : 값 - AMPC(동일 company/segment_std/기간)
매출_excl   = 동일 규칙 (LGES 2026+ 매출에 주의)
```
**3사 비교의 기본(default) 지표는 excl-AMPC 기준.** as-reported와 AMPC 기여분은 별도 레이어로 표시한다.

## 3. 기간 — `period`

`FY`(연간) 또는 `1Q`~`4Q`(분기), `fy`는 회계연도. 추출 범위: 분기는 1Q25 이후, 연간은 FY2024~FY2028. 리포트 발간일 기준 이미 발표된 분기 값은 애널리스트가 인용한 실적(사실상 actual)이며, 미발표 분기는 추정치다 — 발간일(date)과 대상 기간을 대조해 구분한다.

## 4. Actuals (정답지) 분리

- 회사 IR 자료 원본: `actuals/` (LGES 실적설명회·스크립트, 삼성SDI IR)
- 추출 결과: `index/actuals.csv` — 컨센서스 적중률 계산의 기준값
- SK온은 IR 미보유 → 애널리스트 리포트에 인용된 발표 실적의 중앙값을 사실상 actual로 사용하고 출처를 명시한다.

## 5. 투자의견 표준화

매수/BUY/Outperform → `매수`, 중립/HOLD/Marketperform/Neutral → `중립`, 매도/SELL/Underperform → `매도`. 산업 리포트는 null + `industry_views` 사용.

## 6. 스탠스·이슈 통제어휘

`stance_score`: **-10 ~ +10** (2026-07 스케일 확장, 구버전 -2~+2는 전량 재채점 완료).
채점 기준표(rubric) — 부호는 방향, 크기는 확신·강도:
| 크기 | 기준 |
|---|---|
| ±1~2 | 스치듯 언급된 뉘앙스, 명확한 근거 없음 |
| ±3~4 | 방향성 있는 코멘트, 근거 1개 수준 |
| ±5~6 | 명확한 방향 + 구체 근거(수치·일정·고객사) |
| ±7~8 | 핵심 투자논지 수준의 강한 확신, 추정치에 반영됨 |
| ±9~10 | 극단적 콜 — 목표가 대폭 변경 동반, 구조적 단정 |
| 0 | 중립·양비론 |
이슈 태그: LFP, 46파이, ESS, 북미CAPEX, 수율, AMPC, 파우치, 전고체, 밸류에이션, 소형전지, 유럽EV, 북미EV, 중국경쟁, 관세, 로봇, 배터리판매량. (신규 필요 시 추가하되 유사어 통합)

산업 리포트는 `industry_views`: {scope(글로벌EV수요/북미ESS/유럽EV/중국경쟁/메탈가격/K배터리 등), fy, metric, value, unit, direction(-2~+2), summary, page} + `top_picks`.

## 7. 중복 리포트 처리

동일 내용의 언어판(영/한) 등 중복 리포트는 이중 집계를 유발하므로 인제스트 전에 걸러낸다.
- **탐지**: `tools/check_duplicates.py` — 같은 (하우스, 커버리지) + 발간일 2일 이내를 후보로 플래그. 신규 인제스트 전 `--new-only`로 실행.
- **판정**: 후보의 제목·첫 페이지를 대조해 내용 동일 여부 확인 (언어만 다르면 중복).
- **처리**: 삭제하지 않는다 — 한국어판 1건만 유지, 나머지는 `archive/duplicates/`로 이동(git mv)하고 manifest 항목에 `duplicate_of: <유지한 report_id>` 기록. `build_indexes.py`가 해당 항목을 인덱스·MD에서 자동 제외한다.

## 8. 산업리포트 스키마 v3 (2026-07)

산업리포트는 `schema_version: 3`부터 industry_views를 용도별 테이블 2개로 분리한다.

### demand_forecasts (정량 수요 전망 — 지역별 수요 View·리비전 트래커의 원천)
`{region, application, metric, fy, value, value_prev, unit, basis, page}`
- region: 글로벌|북미|유럽|중국|한국|기타 / application: EV|ESS|합계 (결합 문자열 금지)
- metric: 수요량(GWh)|판매대수(천대·만대)|성장률(%)|침투율(%)|실적치(발표된 과거 실측)
- **표에 있는 모든 연도를 수집한다** (2023~2035, 중간연도 생략 금지)
- value_prev: 리포트가 '기존 전망 대비' 변경을 명시한 경우의 직전 전망치

### themes (정성 방향성 — 테마 로테이션 맵·논거 대전의 원천)
`{theme(6절 통제어휘), direction(-10~+10, 6절 rubric), bull, bear, summary, page}`
- bull/bear: 그 테마의 강세/약세 논거 각 1~2문장 (한쪽만 있으면 다른 쪽 null)

인덱스: demand_forecasts.csv, themes.csv 신설. 기존 인덱스 무변경(하위호환).
기업 리포트의 industry_views(명시적 산업 전망)는 기존대로 industry_views.csv에 유지.
