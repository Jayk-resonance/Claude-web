#!/usr/bin/env python3
"""Build ESS-specific enriched indexes without breaking legacy indexes.

Inputs
- .staging/*.json: future ingests may contain extended demand_forecasts + company_metrics
- projects/ess_market_intelligence/backfill_15.json: curated backfill from existing MD/index

Outputs
- index/demand_forecasts_v2.csv
- index/company_metrics.csv

Legacy `index/demand_forecasts.csv` is intentionally untouched for dashboard compatibility.
"""
import csv
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING = os.path.join(ROOT, ".staging")
INDEX = os.path.join(ROOT, "index")
BACKFILL = os.path.join(ROOT, "projects", "ess_market_intelligence", "backfill_15.json")

DEMAND_FIELDS = [
    "report_id", "date", "house",
    "region", "application", "region_raw", "region_std",
    "application_raw", "application_std", "application_detail",
    "metric", "forecast_type", "fy", "value", "value_low", "value_high", "value_prev", "unit",
    "basis", "source_org", "source_name", "source_type", "source_page", "verification_status",
]

COMPANY_FIELDS = [
    "report_id", "date", "house", "company", "entity_type", "company_group",
    "region_raw", "region_std", "application_raw", "application_std", "application_detail",
    "metric", "fy", "value", "value_low", "value_high", "unit", "basis",
    "source_org", "source_type", "source_page", "verification_status",
]

REGION_MAP = {
    "글로벌": "Global", "전세계": "Global", "Global": "Global",
    "북미": "North America", "North America": "North America",
    "미국": "US", "US": "US", "USA": "US",
    "유럽": "Europe", "EU": "Europe", "Europe": "Europe",
    "중국": "China", "China": "China",
    "한국": "Korea", "Korea": "Korea",
}

APP_STD = {"Total", "Grid", "Data Center", "C&I", "Residential", "Other"}
FORECAST_TYPES = {"demand", "shipment", "installation", "capacity", "growth_rate", "penetration", "market_share", "actual", "other"}
SOURCE_TYPES = {"broker_estimate", "external_republication", "market_consensus", "reported_observation", "company_guidance", "other"}
VERIFY_TYPES = {"pdf_verified", "md_backfill", "needs_pdf_review"}
ENTITY_TYPES = {"company", "group"}
COMPANY_GROUPS = {"K-battery", "China", "Japan", "Europe-US", "Other"}
COMPANY_METRICS = {"capacity", "shipment", "backlog", "order_target", "market_share", "production", "utilization", "ampc_volume", "other"}


def load_reports():
    reports = []
    for path in sorted(glob.glob(os.path.join(STAGING, "*.json"))):
        name = os.path.basename(path)
        if name == "manifest.json" or name.startswith("actuals_") or name.startswith("viewnarr_"):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                r = json.load(f)
        except Exception:
            continue
        if r.get("report_id"):
            reports.append(r)
    return reports


def report_meta(reports):
    return {r["report_id"]: {"date": r.get("date"), "house": r.get("house")} for r in reports}


def normalize_demand(row, rid=None, date=None, house=None):
    x = dict(row)
    x["report_id"] = x.get("report_id") or rid
    x["date"] = x.get("date") or date
    x["house"] = x.get("house") or house
    raw_region = x.get("region_raw") or x.get("region")
    x["region_raw"] = raw_region
    x["region_std"] = x.get("region_std") or REGION_MAP.get(raw_region, "Other")
    x["region"] = x.get("region") or raw_region
    x["application"] = x.get("application") or "ESS"
    x["application_raw"] = x.get("application_raw") or ("ESS 전체" if x.get("application") == "ESS" else x.get("application"))
    x["application_std"] = x.get("application_std") or ("Total" if x.get("application") == "ESS" else "Other")
    x["application_detail"] = x.get("application_detail")
    x["forecast_type"] = x.get("forecast_type") or infer_forecast_type(x.get("metric"))
    x["value_low"] = x.get("value_low")
    x["value_high"] = x.get("value_high")
    x["source_org"] = x.get("source_org") or x.get("house")
    x["source_name"] = x.get("source_name")
    x["source_type"] = x.get("source_type") or "broker_estimate"
    x["source_page"] = x.get("source_page") if x.get("source_page") is not None else x.get("page")
    x["verification_status"] = x.get("verification_status") or "pdf_verified"
    return x


def normalize_company(row, rid=None, date=None, house=None):
    x = dict(row)
    x["report_id"] = x.get("report_id") or rid
    x["date"] = x.get("date") or date
    x["house"] = x.get("house") or house
    raw_region = x.get("region_raw")
    x["region_std"] = x.get("region_std") or REGION_MAP.get(raw_region, "Other")
    x["application_raw"] = x.get("application_raw") or "ESS 전체"
    x["application_std"] = x.get("application_std") or "Total"
    x["application_detail"] = x.get("application_detail")
    x["entity_type"] = x.get("entity_type") or "company"
    x["company_group"] = x.get("company_group") or "Other"
    x["source_org"] = x.get("source_org") or x.get("house")
    x["source_type"] = x.get("source_type") or "broker_estimate"
    x["source_page"] = x.get("source_page") if x.get("source_page") is not None else x.get("page")
    x["verification_status"] = x.get("verification_status") or "pdf_verified"
    return x


def infer_forecast_type(metric):
    m = (metric or "").lower()
    if "설치" in m: return "installation"
    if "출하" in m: return "shipment"
    if "capa" in m or "capacity" in m or "생산능력" in m: return "capacity"
    if "성장" in m or "증가율" in m: return "growth_rate"
    if "점유" in m or "m/s" in m: return "market_share"
    if "비중" in m or "침투" in m: return "penetration"
    if "수요" in m: return "demand"
    return "other"


def validate_demand(x):
    errs = []
    if x.get("application") == "ESS" and x.get("application_std") not in APP_STD:
        errs.append(f"application_std={x.get('application_std')}")
    if x.get("forecast_type") not in FORECAST_TYPES:
        errs.append(f"forecast_type={x.get('forecast_type')}")
    if x.get("source_type") not in SOURCE_TYPES:
        errs.append(f"source_type={x.get('source_type')}")
    if x.get("verification_status") not in VERIFY_TYPES:
        errs.append(f"verification_status={x.get('verification_status')}")
    if x.get("value") is None and x.get("value_low") is None and x.get("value_high") is None:
        errs.append("no numeric value/range")
    return errs


def validate_company(x):
    errs = []
    if x.get("entity_type") not in ENTITY_TYPES: errs.append(f"entity_type={x.get('entity_type')}")
    if x.get("company_group") not in COMPANY_GROUPS: errs.append(f"company_group={x.get('company_group')}")
    if x.get("application_std") not in APP_STD: errs.append(f"application_std={x.get('application_std')}")
    if x.get("metric") not in COMPANY_METRICS: errs.append(f"metric={x.get('metric')}")
    if x.get("verification_status") not in VERIFY_TYPES: errs.append(f"verification_status={x.get('verification_status')}")
    return errs


def dedup(rows, fields):
    out, seen = [], set()
    for r in rows:
        key = tuple(str(r.get(k)) for k in fields)
        if key not in seen:
            out.append(r); seen.add(key)
    return out


def main(check_only=False):
    reports = load_reports()
    meta = report_meta(reports)
    demand, company = [], []

    # Future ingests from staging.
    for r in reports:
        for d in r.get("demand_forecasts", []) or []:
            demand.append(normalize_demand(d, r["report_id"], r.get("date"), r.get("house")))
        for c in r.get("company_metrics", []) or []:
            company.append(normalize_company(c, r["report_id"], r.get("date"), r.get("house")))

    # Curated 15-report backfill.
    if os.path.exists(BACKFILL):
        with open(BACKFILL, encoding="utf-8") as f:
            b = json.load(f)
        for d in b.get("demand_forecasts", []):
            m = meta.get(d.get("report_id"), {})
            demand.append(normalize_demand(d, date=m.get("date"), house=m.get("house")))
        for c in b.get("company_metrics", []):
            m = meta.get(c.get("report_id"), {})
            company.append(normalize_company(c, date=m.get("date"), house=m.get("house")))

    demand = dedup(demand, ["report_id","region_std","application_std","application_detail","metric","forecast_type","fy","value","value_low","value_high","unit","source_org"])
    company = dedup(company, ["report_id","company","region_std","application_std","application_detail","metric","fy","value","unit"])

    errors = []
    for x in demand:
        for e in validate_demand(x): errors.append(f"[demand {x.get('report_id')}] {e}")
    for x in company:
        for e in validate_company(x): errors.append(f"[company {x.get('report_id')}] {e}")

    print(f"ESS demand rows={len(demand)}, company rows={len(company)}, validation={len(errors)}")
    for e in errors: print(" ", e)
    if check_only:
        return 1 if errors else 0

    os.makedirs(INDEX, exist_ok=True)
    with open(os.path.join(INDEX, "demand_forecasts_v2.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DEMAND_FIELDS, extrasaction="ignore")
        w.writeheader()
        for x in sorted(demand, key=lambda z: (z.get("date") or "", z.get("report_id") or "", z.get("fy") or 0)):
            w.writerow({k: x.get(k) for k in DEMAND_FIELDS})

    with open(os.path.join(INDEX, "company_metrics.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COMPANY_FIELDS, extrasaction="ignore")
        w.writeheader()
        for x in sorted(company, key=lambda z: (z.get("date") or "", z.get("report_id") or "", z.get("company") or "", z.get("fy") or 0)):
            w.writerow({k: x.get(k) for k in COMPANY_FIELDS})

    print("wrote index/demand_forecasts_v2.csv and index/company_metrics.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
