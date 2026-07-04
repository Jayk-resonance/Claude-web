#!/usr/bin/env python3
"""인덱스 -> 대시보드 데이터셋 (projects/dashboard/data.json).

기능별 블록:
  f1_quarterly   분기별 3사 재무 비교 (부문 포함, QoQ/YoY, 드라이버 설명)
  f2_stance      이슈별 3사 스탠스 매트릭스
  f3_views       증권사별 View 변화 (목표주가/의견 시계열)
  f4_accuracy    컨센서스 적중률 (1Q26 + FY2025 빈티지)
  f5_outliers    이견/아웃라이어 탐지
  f6_dotplots    FOMC식 점도표 (3사 영업이익 / 산업 지역별)

정규화: NORMALIZATION.md 준수. OP_incl = excl + AMPC(동일 키) 파생.
"""
import json, csv, os, statistics as st, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "index")
OUT = os.path.join(ROOT, "projects", "dashboard")
os.makedirs(OUT, exist_ok=True)

COMPANIES = ["LGES", "삼성SDI", "SK온"]
ANNOUNCE = {("LGES", 2026, "1Q"): "2026-04-08", ("삼성SDI", 2026, "1Q"): "2026-04-28"}

est = list(csv.DictReader(open(f"{IDX}/estimates.csv", encoding="utf-8")))
stances = list(csv.DictReader(open(f"{IDX}/stances.csv", encoding="utf-8")))
actuals = list(csv.DictReader(open(f"{IDX}/actuals.csv", encoding="utf-8")))
iviews = list(csv.DictReader(open(f"{IDX}/industry_views.csv", encoding="utf-8")))
reports = [json.loads(l) for l in open(f"{IDX}/reports.jsonl", encoding="utf-8")]
drivers = list(csv.DictReader(open(f"{IDX}/drivers.csv", encoding="utf-8")))

CUR = os.path.join(OUT, "narratives.json")  # 큐레이션 내러티브 (수기)
narratives = json.load(open(CUR, encoding="utf-8")) if os.path.exists(CUR) else {}

for e in est:
    e["value"] = float(e["value"]) if e["value"] else None


def op_incl(rows_one_report, company, seg, fy, period):
    """한 리포트 내에서 AMPC 포함 영업이익 도출 (기준 통일)."""
    sel = [r for r in rows_one_report if r["company"] == company
           and r["segment_std"] == seg and r["fy"] == str(fy) and r["period"] == period]
    op = {r["ampc_basis"]: r["value"] for r in sel if r["metric"] == "영업이익"}
    ampc = next((r["value"] for r in sel if r["metric"] == "AMPC"), None)
    if ampc is None:  # 전사 AMPC로 폴백 (seg=전사일 때만 의미)
        ampc = next((r["value"] for r in rows_one_report
                     if r["company"] == company and r["fy"] == str(fy)
                     and r["period"] == period and r["metric"] == "AMPC"
                     and r["segment_std"] == "전사"), None)
    if "incl" in op:
        return op["incl"], "incl"
    if "excl" in op and ampc is not None:
        return op["excl"] + ampc, "derived(excl+AMPC)"
    if "incl_unknown" in op:
        return op["incl_unknown"], "incl_unknown"
    if "excl" in op:
        return op["excl"], "excl_only"
    if "na" in op:
        return op["na"], "na"
    return None, None


by_report = collections.defaultdict(list)
for e in est:
    by_report[e["report_id"]].append(e)
rmeta = {r["report_id"]: r for r in reports}

# ---------- F1: 분기별 실적 비교 ----------
def actual_grid():
    grid = collections.defaultdict(dict)  # (company,fy,period) -> {seg/metric: val}
    for a in actuals:
        if a["period"] == "FY":
            continue
        k = (a["company"], int(a["fy"]), a["period"])
        grid[k][f"{a['segment_std']}|{a['metric']}|{a.get('ampc_basis','na')}"] = float(a["value"])
    return grid

# SK온 분기 실적: 발간일 기준 이미 발표된 분기의 애널리스트 인용값 중앙값
def skon_quarters():
    out = {}
    for fy, period, cutoff in [(2025,"1Q","2025-04-30"),(2025,"2Q","2025-08-01"),
                               (2025,"3Q","2025-11-01"),(2025,"4Q","2026-02-01"),
                               (2026,"1Q","2026-05-01")]:
        for metric in ["매출","영업이익"]:
            vals = [e["value"] for e in est if e["company"]=="SK온"
                    and e["segment_std"]=="배터리합계" and e["fy"]==str(fy)
                    and e["period"]==period and e["metric"]==metric
                    and e["date"] >= cutoff and e["value"] is not None]
            if vals:
                out[f"{fy}|{period}|{metric}"] = {"value": round(st.median(vals),1),
                                                  "n_sources": len(vals), "method": "애널리스트 인용 중앙값"}
    return out

f1 = {"actuals_grid": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in actual_grid().items()},
      "skon_quarters": skon_quarters(),
      "company_drivers": [dict(d) for d in drivers],
      "narratives": narratives.get("f1", {})}

# ---------- F2: 이슈별 스탠스 매트릭스 ----------
ISSUE_ALIAS = {"배터리판매량":"판매량","북미EV":"북미수요","유럽EV":"유럽수요"}
mat = collections.defaultdict(list)
for s in stances:
    comp = s["company"]
    if comp not in COMPANIES:
        continue
    issue = ISSUE_ALIAS.get(s["issue"], s["issue"])
    mat[(issue, comp)].append({"house": s["house"], "date": s["date"],
                               "score": float(s["stance_score"]) if s["stance_score"] else 0,
                               "summary": s["summary"], "report_id": s["report_id"]})
f2 = []
for (issue, comp), items in mat.items():
    items.sort(key=lambda x: x["date"])
    recent = [i for i in items if i["date"] >= "2026-01-01"] or items
    f2.append({"issue": issue, "company": comp,
               "median_recent": st.median([i["score"] for i in recent]),
               "n": len(items), "items": items})

# ---------- F3: 증권사별 View 변화 ----------
f3 = collections.defaultdict(list)
for r in sorted(reports, key=lambda x: x["date"]):
    if r["coverage"] not in COMPANIES:
        continue
    srows = [s for s in stances if s["report_id"] == r["report_id"]]
    avg = round(st.mean([float(s["stance_score"]) for s in srows]), 2) if srows else None
    f3[f"{r['house']}|{r['coverage']}"].append(
        {"date": r["date"], "opinion": r["opinion"], "target_price": r["target_price"],
         "avg_stance": avg, "report_id": r["report_id"], "summary": r["summary"][:120]})
f3 = dict(f3)

# ---------- F4: 컨센서스 적중률 ----------
f4 = {"events": []}
for (comp, fy, period), adate in ANNOUNCE.items():
    act_rows = [a for a in actuals if a["company"] == comp and a["fy"] == str(fy)
                and a["period"] == period and a["segment_std"] == "전사"]
    act = {}
    for a in act_rows:
        act.setdefault(a["metric"], float(a["value"]))
    if not act:
        continue
    preds = []
    for rid, rows in by_report.items():
        rm = rmeta.get(rid)
        if not rm or rm["date"] >= adate or rm["coverage"] != comp:
            continue
        if rm["date"] < "2026-02-01":
            continue  # 직전 프리뷰 시즌만
        op, basis = op_incl(rows, comp, "전사", fy, period)
        rev = next((r["value"] for r in rows if r["company"] == comp
                    and r["segment_std"] == "전사" and r["fy"] == str(fy)
                    and r["period"] == period and r["metric"] == "매출"), None)
        if op is None and rev is None:
            continue
        e = {"house": rm["house"], "date": rm["date"], "report_id": rid,
             "op_est": op, "op_basis": basis, "rev_est": rev}
        if op is not None and act.get("영업이익") is not None:
            e["op_err"] = round(op - act["영업이익"], 1)
        if rev is not None and act.get("매출") is not None:
            e["rev_err_pct"] = round((rev - act["매출"]) / act["매출"] * 100, 1)
        preds.append(e)
    f4["events"].append({"company": comp, "fy": fy, "period": period,
                         "announce_date": adate, "actual": act, "preds": preds})

# FY2025 빈티지 적중률 (2023~25년 리포트의 FY2025 전망 vs 실제)
ACT_FY25 = {"LGES": {"매출": 23672, "영업이익": 1346}, "삼성SDI": {"매출": 13267, "영업이익": -1722}}
vint = []
for rid, rows in by_report.items():
    rm = rmeta.get(rid)
    if not rm or rm["date"] >= "2025-10-01":
        continue
    for comp in ["LGES", "삼성SDI"]:
        op, basis = op_incl(rows, comp, "전사", 2025, "FY")
        if op is None:
            continue
        vint.append({"house": rm["house"], "date": rm["date"], "report_id": rid,
                     "company": comp, "op_est": op, "op_basis": basis,
                     "op_actual": ACT_FY25[comp]["영업이익"],
                     "op_err": round(op - ACT_FY25[comp]["영업이익"], 1)})
f4["fy2025_vintage"] = sorted(vint, key=lambda x: x["date"])

# ---------- F5: 아웃라이어 ----------
f5 = {"estimate_outliers": [], "stance_outliers": []}
for comp, seg in [("LGES","전사"),("삼성SDI","전사"),("SK온","배터리합계")]:
    for fy in [2026, 2027]:
        latest = {}
        for rid, rows in by_report.items():
            rm = rmeta.get(rid)
            if not rm or rm["coverage"] != comp or rm["date"] < "2026-03-01":
                continue
            op, basis = op_incl(rows, comp, seg, fy, "FY")
            if op is None or basis in ("excl_only",):
                continue
            cur = latest.get(rm["house"])
            if not cur or rm["date"] > cur["date"]:
                latest[rm["house"]] = {"house": rm["house"], "date": rm["date"],
                                       "op": op, "basis": basis, "report_id": rid}
        vals = [v["op"] for v in latest.values()]
        if len(vals) >= 3:
            med = st.median(vals)
            for v in latest.values():
                v["dev_from_median"] = round(v["op"] - med, 1)
            f5["estimate_outliers"].append(
                {"company": comp, "fy": fy, "median": med, "n_houses": len(vals),
                 "houses": sorted(latest.values(), key=lambda x: -abs(x["dev_from_median"]))})
for row in f2:
    if row["n"] >= 3:
        scores = [i["score"] for i in row["items"] if i["date"] >= "2026-01-01"]
        if len(scores) >= 3:
            med = st.median(scores)
            outl = [i for i in row["items"] if i["date"] >= "2026-01-01"
                    and abs(i["score"] - med) >= 2]
            if outl:
                f5["stance_outliers"].append({"issue": row["issue"], "company": row["company"],
                                              "median": med, "outliers": outl})

# ---------- F6: 점도표 ----------
f6 = {"op_dots": [], "industry_dots": []}
for comp, seg in [("LGES","전사"),("삼성SDI","전사"),("SK온","배터리합계")]:
    dots = []
    for rid, rows in by_report.items():
        rm = rmeta.get(rid)
        if not rm:
            continue
        for fy in [2025, 2026, 2027, 2028]:
            op, basis = op_incl(rows, comp, seg, fy, "FY")
            if op is not None:
                dots.append({"house": rm["house"], "report_date": rm["date"],
                             "fy": fy, "op": op, "basis": basis, "report_id": rid})
    f6["op_dots"].append({"company": comp, "segment": seg, "dots": dots})
for v in iviews:
    if v["direction"]:
        f6["industry_dots"].append({"house": v["house"], "date": v["date"],
                                    "scope": v["scope"], "fy": v["fy"],
                                    "direction": float(v["direction"]),
                                    "value": v["value"], "unit": v["unit"],
                                    "summary": v["summary"], "report_id": v["report_id"]})

data = {"meta": {"built_from": "battery-reports index v2", "n_reports": len(reports),
                 "n_estimates": len(est), "houses": sorted({r['house'] for r in reports}),
                 "period": f"{min(r['date'] for r in reports)} ~ {max(r['date'] for r in reports)}",
                 "note_basis": "영업이익 비교는 AMPC 포함(incl) 기준 통일. excl만 있는 경우 AMPC 가산 파생(derived). LGES 매출은 1Q26부터 AMPC 병합 표시(IR 재작성 기준)."},
        "f1_quarterly": f1, "f2_stance": f2, "f3_views": f3,
        "f4_accuracy": f4, "f5_outliers": f5, "f6_dotplots": f6}
json.dump(data, open(f"{OUT}/data.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"data.json 생성: {os.path.getsize(f'{OUT}/data.json')//1024}KB")
print(f"f2 {len(f2)}셀 / f3 {len(f3)}시리즈 / f4 이벤트 {len(f4['events'])}+빈티지 {len(f4['fy2025_vintage'])}행"
      f" / f5 추정치 {len(f5['estimate_outliers'])}·스탠스 {len(f5['stance_outliers'])} / f6 dots {sum(len(d['dots']) for d in f6['op_dots'])}")
