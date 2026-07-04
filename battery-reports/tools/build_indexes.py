#!/usr/bin/env python3
"""스테이징 JSON -> 표준 MD + 인덱스 재빌드 (스키마 v2).

사용법:
  python3 tools/build_indexes.py           # 검증 + 렌더 + 인덱스
  python3 tools/build_indexes.py --check   # 검증만 (파일 안 씀)

입력:  .staging/<report_id>.json (리포트), .staging/actuals_*.json (IR)
출력:  reports/<YYYY>/<report_id>.md
       index/reports.jsonl, estimates.csv, stances.csv,
       industry_views.csv, actuals.csv, drivers.csv
"""
import json, csv, os, sys, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING = os.path.join(ROOT, ".staging")
SEG_STD = {"전사", "배터리합계", "소형", "중대형", "EV", "ESS", "전자재료", "기타"}
AMPC_BASIS = {"excl", "incl", "incl_unknown", "na"}
PERIODS = {"FY", "1Q", "2Q", "3Q", "4Q"}
OPINIONS = {"매수", "중립", "매도", None}

warnings = []


def warn(rid, msg):
    warnings.append(f"[{rid}] {msg}")


def validate(r):
    rid = r.get("report_id", "?")
    for k in ["report_id", "date", "house", "coverage", "report_type", "body"]:
        if not r.get(k):
            warn(rid, f"필수 필드 누락: {k}")
    if r.get("opinion") not in OPINIONS:
        warn(rid, f"opinion 비표준: {r.get('opinion')}")
    for e in r.get("estimates", []):
        if e.get("segment_std") == "AMPC":  # 구버전 흔적 교정
            e["segment_std"] = "전사"
            e["metric"] = "AMPC"
        if e.get("segment_std") not in SEG_STD:
            # 3사 부문이 아닌 밸류체인/소재 등은 '기타'로 강제 (원문 segment 보존)
            warn(rid, f"segment_std '기타'로 강제: {e.get('segment_std')} (segment={e.get('segment')})")
            e["segment_std"] = "기타"
        if e.get("ampc_basis") not in AMPC_BASIS:
            warn(rid, f"ampc_basis 비표준: {e.get('ampc_basis')}")
        if e.get("period") not in PERIODS:
            warn(rid, f"period 비표준: {e.get('period')}")
        if not isinstance(e.get("value"), (int, float)):
            warn(rid, f"value 비숫자: {e.get('value')} ({e.get('metric')})")
        if e.get("unit") not in ("십억원", None):
            warn(rid, f"unit 비표준: {e.get('unit')}")
    for s in r.get("stances", []):
        sc = s.get("stance_score")
        if not isinstance(sc, (int, float)) or not -2 <= sc <= 2:
            warn(rid, f"stance_score 범위 밖: {sc}")


def yflow(items, keys):
    out = []
    for it in items:
        parts = []
        for k in keys:
            v = it.get(k)
            if isinstance(v, str):
                v = '"' + v.replace('"', "'").replace("\n", " ") + '"'
            elif v is None:
                v = "null"
            parts.append(f"{k}: {v}")
        out.append("  - {" + ", ".join(parts) + "}")
    return "\n".join(out) if out else "  []"


def render_md(r):
    b = r["body"]
    fm = ["---"]
    for k in ["report_id", "date", "house", "analyst", "coverage", "report_type", "opinion"]:
        v = r.get(k)
        fm.append(f"{k}: {'null' if v is None else v}")
    fm.append(f"target_price: {r.get('target_price') or 'null'}")
    fm.append(f"prev_target_price: {r.get('prev_target_price') or 'null'}")
    fm.append("estimates:")
    fm.append(yflow(r.get("estimates", []),
                    ["company", "segment", "segment_std", "fy", "period",
                     "metric", "value", "unit", "ampc_basis", "page"]))
    fm.append("stances:")
    fm.append(yflow(r.get("stances", []),
                    ["issue", "company", "stance_score", "summary", "page"]))
    if r.get("industry_views"):
        fm.append("industry_views:")
        fm.append(yflow(r["industry_views"],
                        ["scope", "fy", "metric", "value", "unit",
                         "direction", "summary", "page"]))
    fm.append("key_issues: [" + ", ".join(r.get("key_issues", [])) + "]")
    if r.get("top_picks"):
        fm.append("top_picks: [" + ", ".join(r["top_picks"]) + "]")
    fm.append(f"source_pdf: inbox/{r.get('source_file', '')}")
    fm.append("---")
    body = ["", "## 핵심 요약", b.get("summary", ""),
            "", "## 투자의견·목표주가 (도출 근거)", b.get("valuation", ""),
            "", "## 사업부문별 손익", b.get("segment_pl", ""),
            "", "## 이슈별 코멘트", b.get("issue_comments", ""),
            "", "## 리스크 요인", b.get("risks", ""),
            "", "## 원문 인용", b.get("quotes", ""), ""]
    return "\n".join(fm) + "\n" + "\n".join(body)


def main(check_only=False):
    files = sorted(glob.glob(os.path.join(STAGING, "*.json")))
    reports, actuals_sets = [], []
    for p in files:
        name = os.path.basename(p)
        if name == "manifest.json":
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except json.JSONDecodeError as ex:
            warn(name, f"JSON 파싱 실패: {ex}")
            continue
        if name.startswith("actuals_"):
            actuals_sets.append(d)
        else:
            reports.append(d)

    # manifest 대조: 누락 파일
    mf = json.load(open(os.path.join(STAGING, "manifest.json"), encoding="utf-8"))
    have = {r.get("report_id") for r in reports}
    missing = [m["report_id"] for m in mf if m["report_id"] not in have]
    for m in missing:
        warn(m, "스테이징 JSON 없음 (파싱 실패/미완)")
    fmap = {m["report_id"]: m["file"] for m in mf}
    for r in reports:
        r["source_file"] = fmap.get(r["report_id"], r.get("source_pdf", ""))
        validate(r)

    ids = [r["report_id"] for r in reports]
    if len(ids) != len(set(ids)):
        warn("GLOBAL", "report_id 중복 존재")

    print(f"리포트 {len(reports)}건, actuals 세트 {len(actuals_sets)}건, "
          f"누락 {len(missing)}건, 경고 {len(warnings)}건")
    if check_only:
        for w in warnings:
            print(" ", w)
        return 1 if missing else 0

    # --- MD ---
    for r in reports:
        year = r["date"][:4]
        d = os.path.join(ROOT, "reports", year)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, r["report_id"] + ".md"), "w", encoding="utf-8") as f:
            f.write(render_md(r))

    idx = os.path.join(ROOT, "index")

    # --- reports.jsonl ---
    with open(os.path.join(idx, "reports.jsonl"), "w", encoding="utf-8") as f:
        for r in sorted(reports, key=lambda x: x["date"]):
            row = {k: r.get(k) for k in
                   ["report_id", "date", "house", "analyst", "coverage",
                    "report_type", "opinion", "target_price",
                    "prev_target_price", "key_issues", "top_picks"]}
            row["summary"] = r["body"].get("summary", "")
            row["source_pdf"] = "inbox/" + r["source_file"]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # --- estimates.csv ---
    with open(os.path.join(idx, "estimates.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["report_id", "date", "house", "company", "segment", "segment_std",
                    "fy", "period", "metric", "value", "unit", "ampc_basis", "source_page"])
        for r in sorted(reports, key=lambda x: x["date"]):
            for e in r.get("estimates", []):
                w.writerow([r["report_id"], r["date"], r["house"], e.get("company"),
                            e.get("segment"), e.get("segment_std"), e.get("fy"),
                            e.get("period"), e.get("metric"), e.get("value"),
                            e.get("unit"), e.get("ampc_basis"), e.get("page")])

    # --- stances.csv ---
    with open(os.path.join(idx, "stances.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["report_id", "date", "house", "company", "issue",
                    "stance_score", "summary", "source_page"])
        for r in sorted(reports, key=lambda x: x["date"]):
            for s in r.get("stances", []):
                w.writerow([r["report_id"], r["date"], r["house"], s.get("company"),
                            s.get("issue"), s.get("stance_score"),
                            s.get("summary"), s.get("page")])

    # --- industry_views.csv ---
    with open(os.path.join(idx, "industry_views.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["report_id", "date", "house", "scope", "fy", "metric",
                    "value", "unit", "direction", "summary", "source_page"])
        for r in sorted(reports, key=lambda x: x["date"]):
            for v in r.get("industry_views", []) or []:
                w.writerow([r["report_id"], r["date"], r["house"], v.get("scope"),
                            v.get("fy"), v.get("metric"), v.get("value"),
                            v.get("unit"), v.get("direction"),
                            v.get("summary"), v.get("page")])

    # --- actuals.csv + drivers.csv ---
    with open(os.path.join(idx, "actuals.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "fy", "period", "segment", "segment_std", "metric",
                    "value", "unit", "ampc_basis", "source_file", "source_page"])
        for a in actuals_sets:
            for row in a.get("actuals", []):
                w.writerow([a["company"], row.get("fy"), row.get("period"),
                            row.get("segment"), row.get("segment_std"),
                            row.get("metric"), row.get("value"), row.get("unit"),
                            row.get("ampc_basis", "na"),
                            row.get("source_file"), row.get("page")])
    with open(os.path.join(idx, "drivers.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "fy", "period", "segment_std", "summary",
                    "source_file", "source_page"])
        for a in actuals_sets:
            for row in a.get("drivers", []):
                w.writerow([a["company"], row.get("fy"), row.get("period"),
                            row.get("segment_std"), row.get("summary"),
                            row.get("source_file"), row.get("page")])

    print("렌더 완료. 경고 목록:")
    for w_ in warnings:
        print(" ", w_)
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
