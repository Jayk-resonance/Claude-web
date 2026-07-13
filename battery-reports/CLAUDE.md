# CLAUDE.md — battery-reports 작업 지침

이 폴더(`battery-reports/`)에서 작업할 때 세션 시작 시 **자동으로 읽히는 파일**이다.
맥락이 전혀 없는 상태로 첫 명령을 받아도, 이 문서만 따르면 올바른 절차를 밟도록 설계되었다.
루트의 `../CLAUDE.md`(범용 코딩 지침)와 병행 적용한다.

## 이 저장소가 하는 일

2차전지 산업 + 3사(LG에너지솔루션·삼성SDI·SK온) 증권사 리포트를 **재사용 가능한 DB**로 관리한다.
설계 철학은 `README.md` 참조. 핵심 한 줄: **원문(MD) 과 구조화 데이터(인덱스) 를 분리**한다.

## 작업 전 반드시 읽을 문서 (순서대로)

1. `README.md` — 저장소 목적·폴더 구조·비개발자 사용법
2. `schema/template.md` — MD의 표준 양식(= DB 스키마). YAML 필드 정의 + 본문 6개 섹션
3. `schema/NORMALIZATION.md` — 판단 규칙: segment_std 매핑, ampc_basis, stance_score rubric(-10~+10), 이슈 통제어휘, 수요 시리즈 분류, KNOWN_OP_BASIS 자동 교정

인제스트/분석에 들어가기 전에 최소 위 3개를 읽는다. **규칙은 내 기억이 아니라 이 문서들에 있다.**

## 데이터 흐름 (파이프라인)

```
inbox/*.pdf                                    # 원본 PDF (사용자가 넣음)
  │  ── [인제스트: PDF 읽고 프론트매터+본문 추출] ──
  ▼
.staging/<report_id>.json                      # 중간 산출물 (개별 JSON은 gitignore)
  │  ── tools/build_indexes.py ──
  ▼
reports/YYYY/<report_id>.md                    # 표준 MD (영속 DB, 커밋됨)
index/{reports.jsonl,estimates.csv,stances.csv,industry_views.csv,actuals.csv,drivers.csv,demand_forecasts.csv,themes.csv}
  │  ── tools/build_dashboard_data.py ──
  ▼
projects/dashboard/data.json                   # 대시보드 데이터셋
  │  ── tools/assemble_dashboard.py ──
  ▼
projects/dashboard/dashboard.html              # 자립형 최종 결과물
```

`report_id` = 파일명(확장자 제외) = `YYYY-MM-DD_증권사_커버리지` (커버리지: LGES|삼성SDI|SK온|산업).

## 인제스트 절차

사용자가 "inbox의 리포트를 인제스트해줘"라고 하면:

1. **위 3개 문서를 읽는다** (template.md, NORMALIZATION.md 필수).
2. `inbox/`의 대상 PDF를 읽는다. `check_duplicates.py --new-only`로 중복(언어판 등)을 먼저 거른다.
3. 각 PDF를 `.staging/<report_id>.json`으로 추출한다. 키 구조는 기존 staging JSON 1~2개를 대조:
   `report_id,date,house,analyst,coverage,report_type,opinion,target_price,prev_target_price,key_issues,estimates,stances,industry_views,top_picks,body`.
   - 애매한 경계 케이스(스탠스 점수, 세그먼트 매핑, AMPC 표기)는 **유사한 기존 MD를 대조**해 일관성을 맞춘다.
   - 모든 숫자에 `page`를 남긴다 (감사 추적).
4. `python3 tools/build_indexes.py --check` 로 검증만 먼저 돌린다 (파일 안 씀).
5. 통과하면 `python3 tools/build_indexes.py` 로 MD 렌더 + 인덱스 재빌드.
6. 대시보드까지 갱신이 필요하면: `python3 tools/build_dashboard_data.py && python3 tools/assemble_dashboard.py`.

절차가 이 6단계로 짧으므로 별도 INGEST.md는 두지 않는다. 규칙이 두꺼워지면 그때 분리.

**이슈 태깅 주의(자주 헷갈리는 것)**: `AMPC`(미국 정부 IRA 생산세액공제)와 `OEM보상금`(완성차 고객사 수취 보상금 — 최소구매 미달·물량 미납·설비·JV 청산 등 일회성)은 **다른 이슈**다. 한 리포트가 둘 다 다루면 **각각 스탠스 행을 따로** 붙인다(1문장이 여러 이슈면 여러 행). 전체 이슈 통제어휘·구분 기준은 `schema/NORMALIZATION.md §6`.

## 대시보드 재생성

UI/차트 로직 = `projects/dashboard/dashboard_template.html`(코드), 데이터 = `data.json`, 서술 = `narratives.json`.
템플릿의 `/*__DATA__*/` 자리에 data.json이 주입되어 자립형 `dashboard.html`이 나온다.

```
python3 tools/build_dashboard_data.py   # index/ + narratives.json → data.json
python3 tools/assemble_dashboard.py     # template + data.json → dashboard.html
```

같은 인덱스에서 실행하면 결정적으로 같은 결과가 나온다(재해석 개입 없음).

## 운영 규칙

- **원천 불가침**: `reports/`·`index/`는 분석 과정에서 절대 손으로 수정하지 않는다. 분석 결과는 `projects/<이름>/`에만 쓴다. 인덱스는 스크립트로만 재생성한다.
- **표기 오류 교정은 스테이징이 아니라 코드에서**: 실적 확정 기간의 OP basis 교정은 `build_dashboard_data.py`의 `KNOWN_OP_BASIS`, 수요 시리즈 분류는 `demand_curation.py`에서만 수정한다. 원본 인덱스는 건드리지 않는다.
- **.staging/**: 개별 JSON은 gitignore(`.staging/.gitignore`), `manifest.json`만 커밋된다. MD·인덱스가 영속 DB이므로 staging은 재현용 중간물이다.
- **git 브랜치**: 지정된 작업 브랜치에 커밋·푸시한다. 커밋은 반드시 `cd battery-reports` 후 실행(셸 cwd가 리포 루트로 리셋되는 경우 있음). force-push는 거부되니 fast-forward로 정렬.
- **Artifact 재게시**: 대시보드를 Artifact로 다시 올릴 때는 **반드시 기존 URL을 `url` 파라미터로 지정**한다(안 하면 새 URL이 발급됨).

## 현재 상태를 확인하는 법 (숫자를 여기 박지 말 것)

상태값은 시간이 지나면 썩으므로 이 문서에 카운트를 하드코딩하지 않는다. 필요하면 그때 확인한다:

- 리포트 수: `wc -l index/reports.jsonl`
- 커버리지·기간 분포: `index/reports.jsonl` 조회
- 대시보드 버전 이력·최신 커밋: `git log --oneline` (진실의 원천은 git)
- 스키마 버전: `schema/NORMALIZATION.md` 제목줄
