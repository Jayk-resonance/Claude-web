# AGENTS.md — AI 에이전트 진입점

이 저장소에서 작업하는 모든 AI 에이전트(Claude / GPT / Gemini / Cursor 등)가 **가장 먼저 읽는 문서**다.
(Claude Code는 `CLAUDE.md`를 자동 로드하지만, 다른 도구는 읽지 않으므로 이 파일을 표준 진입점으로 둔다.)

## 0. 먼저 확인할 것 — 브랜치

**작업 브랜치: `claude/k-battery-reports-db-rqofsk`**

`main`에는 이 프로젝트가 **없다.** 기본 clone은 `main`을 받으므로, 브랜치를 전환하지 않으면
아무것도 보이지 않는다.

```bash
git clone -b claude/k-battery-reports-db-rqofsk <repo-url>
cd battery-reports        # 프로젝트 루트는 이 하위 폴더
```

## 1. 이 프로젝트

`battery-reports/` — K-배터리 3사(LG에너지솔루션·삼성SDI·SK온) 증권사 리포트를
**재사용 가능한 DB**(표준 MD + 인덱스)로 관리하고, 자립형 HTML 대시보드를 생성한다.

## 2. 작업 전 반드시 읽을 문서 (순서대로)

| 순서 | 문서 | 내용 |
|---|---|---|
| 1 | `battery-reports/CLAUDE.md` | **작업 지침 본문** — 파이프라인, 인제스트 6단계, 운영 규칙, 실적 갱신 체크리스트 |
| 2 | `battery-reports/schema/template.md` | 표준 MD 양식 + **인제스트 입력 형식(staging JSON 스키마)** ← 부록 |
| 3 | `battery-reports/schema/NORMALIZATION.md` | 판단 규칙 — segment_std, ampc_basis, **metric 통제어휘**, stance_score, 이슈 어휘 |
| 4 | `battery-reports/README.md` | 저장소 설계 배경 |

세부 규칙을 이 파일에 복사하지 않는다(내용이 갈라지는 것을 막기 위해). **위 문서가 원본이다.**

## 3. 조용히 데이터를 망가뜨리는 3가지 — 반드시 숙지

에러 없이 진행되면서 데이터가 손상되는 경우들이다. 실제로 발생했던 사고다.

1. **`build_indexes.py`는 `.staging/`을 유일 소스로 `index/`·`reports/`를 전량 덮어쓴다.**
   staging이 없거나 일부만 있는 상태로 돌리면 DB가 비워진다.
   → 지금은 축소 재빌드가 자동 차단된다(종료코드 2). **차단 메시지가 뜨면 `--force`로 뚫지 말고
   staging이 온전한지 먼저 확인한다.**

2. **`metric` 동의어가 갈리면 그 리포트 값이 통째로 누락된다.**
   과거 `매출` vs `매출액` 혼재로 기업 리포트 26건의 매출이 대시보드에서 빠져 있었다.
   → 통제어휘는 `NORMALIZATION.md §2-1`. 인제스트 후 `--check`의 `metric 비표준` 경고를 무시하지 않는다.

3. **`body`의 6개 키 이름이 틀리면 해당 MD 섹션이 오류 없이 빈 채로 생성된다.**
   → 정확한 키는 `template.md` 부록 참조.

## 4. 인제스트 최소 절차

```bash
cd battery-reports
# 1) PDF → .staging/<report_id>.json  (형식: schema/template.md 부록)
python3 tools/build_indexes.py --check    # 2) 검증만 (파일 안 씀) — 경고 확인
python3 tools/build_indexes.py            # 3) 표준 MD + 인덱스 재생성
python3 tools/build_dashboard_data.py     # 4) 대시보드 데이터 ([STALE] 경고 확인)
python3 tools/assemble_dashboard.py       # 5) 자립형 dashboard.html
```

전체 절차·주의사항은 `CLAUDE.md`의 «인제스트 절차» 참조.
새 분기 실적이 발표된 뒤에는 «새 실적 발표 시 갱신 체크리스트»를 반드시 수행한다.

## 5. 여러 에이전트가 나눠 작업할 때 (권장 분업)

토큰 부담으로 여러 LLM이 나눠 작업하는 경우:

- **분산 가능(토큰 소모 큼)**: PDF 판독 → `.staging/<report_id>.json` **생성까지만**.
  각 에이전트에 위 2·3번 문서와 기존 staging JSON 1~2개를 예시로 함께 제공한다.
- **한 곳에서만 실행**: `build_indexes.py` 이후 단계(인덱스 재생성·대시보드 빌드·헤드메시지 갱신).
  빌드를 한 세션에서만 돌리면 3장 1번 사고를 원천 차단할 수 있다.

staging JSON은 git으로 추적되므로, 각자 만든 결과를 커밋해 공유하면 된다.

## 6. 공통 규칙

- **원천 불가침**: `reports/`·`index/`를 손으로 고치지 않는다. 스크립트로만 재생성한다.
- 표기 오류 교정은 스테이징이 아니라 **코드**에서 한다(`KNOWN_OP_BASIS`, `METRIC_STD`, `demand_curation.py`).
- 커밋은 지정 작업 브랜치에 한다. 커밋 전 `cd battery-reports`.
- 루트 `CLAUDE.md`는 언어 무관 범용 코딩 지침이다(단순함 우선, 최소 변경). 함께 적용한다.
