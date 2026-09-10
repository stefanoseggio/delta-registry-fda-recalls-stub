"""
FDA + EMA drug safety sample puller (free stub).

Pulls a small, one-off sample of real records from two independent public
regulatory feeds and combines them into a single normalized list:

  - FDA openFDA drug enforcement (recall) API:
      https://api.fda.gov/drug/enforcement.json
  - EMA Direct Healthcare Professional Communications (DHPC) JSON export:
      https://www.ema.europa.eu/en/documents/report/dhpc-output-json-report_en.json

Both are free, public, unauthenticated feeds - no API key or signup is
required for either request this script makes.

This is a ONE-OFF, single-run script. It does not schedule itself, does
not track changes between runs (no delta / status-change detection), and
does not retry failed requests. See the "What this doesn't do" section of
README.md for the full list, and
https://apify.com/stefano_seggio/actor-22-drug-safety-recalls-monitor
for the hosted version that adds those things.
"""

import json
import sys
from datetime import datetime, timezone

import requests

FDA_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"
EMA_DHPC_JSON_URL = "https://www.ema.europa.eu/en/documents/report/dhpc-output-json-report_en.json"

# Cap per source, so the combined sample stays around ~20 records total.
MAX_PER_SOURCE = 10
OUTPUT_FILE = "sample_output.json"
REQUEST_TIMEOUT = 30  # seconds


def fetch_fda_sample(limit: int, scraped_at: str) -> list:
    """One-off GET against the real openFDA drug enforcement endpoint,
    newest first by report_date. No pagination beyond this single request,
    no retry: a failed request is reported and this source is simply
    skipped, not queued or retried."""
    params = {"sort": "report_date:desc", "limit": str(limit)}

    try:
        response = requests.get(FDA_ENFORCEMENT_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: request to openFDA failed: {exc}")
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        print(f"ERROR: openFDA response was not valid JSON: {exc}")
        return []

    raw_records = payload.get("results", [])
    normalized = []
    for rec in raw_records:
        normalized.append({
            "recordSource": "fda_enforcement",
            "jurisdiction": "US",
            "scraped_at": scraped_at,
            "recipient_or_defendant_name": rec.get("recalling_firm"),
            "category_or_type": rec.get("product_type"),
            "status_or_estado": rec.get("status") or None,
            "reference_number": rec.get("recall_number"),
            "classification": rec.get("classification"),
            "reason_for_recall": rec.get("reason_for_recall"),
            "source_url": FDA_ENFORCEMENT_URL,
        })
    return normalized


def fetch_ema_sample(limit: int, scraped_at: str) -> list:
    """One-off GET of the real EMA DHPC JSON export. EMA does not offer a
    query or limit parameter on this export - it returns a full snapshot
    per request - so this downloads the whole file once and keeps only the
    first `limit` records client-side. No retry on failure."""
    try:
        response = requests.get(EMA_DHPC_JSON_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: request to EMA failed: {exc}")
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        print(f"ERROR: EMA response was not valid JSON: {exc}")
        return []

    raw_records = payload.get("data", [])[:limit]
    normalized = []
    for rec in raw_records:
        normalized.append({
            "recordSource": "ema_dhpc",
            "jurisdiction": "EU",
            "scraped_at": scraped_at,
            "recipient_or_defendant_name": rec.get("name_of_medicine"),
            "category_or_type": rec.get("dhpc_type"),
            "status_or_estado": rec.get("regulatory_outcome") or None,
            "reference_number": rec.get("procedure_number") or None,
            "active_substances": rec.get("active_substances"),
            "source_url": rec.get("dhpc_url"),
        })
    return normalized


def main() -> None:
    scraped_at = datetime.now(timezone.utc).isoformat()

    print(f"Fetching up to {MAX_PER_SOURCE} records from FDA openFDA ({FDA_ENFORCEMENT_URL}) ...")
    fda_records = fetch_fda_sample(MAX_PER_SOURCE, scraped_at)
    print(f"  -> got {len(fda_records)} FDA record(s)")

    print(f"Fetching up to {MAX_PER_SOURCE} records from EMA DHPC export ({EMA_DHPC_JSON_URL}) ...")
    ema_records = fetch_ema_sample(MAX_PER_SOURCE, scraped_at)
    print(f"  -> got {len(ema_records)} EMA record(s)")

    combined = fda_records + ema_records

    if not combined:
        print("No records fetched from either source. Nothing written.")
        sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(combined)} combined record(s) to {OUTPUT_FILE}")
    print("First record:")
    print(json.dumps(combined[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
