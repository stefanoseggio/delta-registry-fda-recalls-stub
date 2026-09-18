# Drug Safety Sample Puller (free stub)

This is a small, free, open-source Python script that does one thing: it makes a single, one-off pull from the same two real public regulatory feeds used by the paid "Drug Safety & Recall Monitor" Apify Actor - the FDA's **openFDA drug enforcement API** (`https://api.fda.gov/drug/enforcement.json`) and the EMA's **Direct Healthcare Professional Communications (DHPC) JSON export** (`https://www.ema.europa.eu/en/documents/report/dhpc-output-json-report_en.json`) - normalizes both into a shared set of fields, and saves a small combined JSON sample (up to 20 records: 10 per source) to a local file. Both feeds are free and unauthenticated; no API key or signup is required to run this script. It runs once, on demand, from your own machine - it is not a monitoring service, a scheduler, or a delta-tracking tool; see [What this doesn't do](#what-this-doesnt-do) below.

## Setup & run

```bash
pip install -r requirements.txt
python main.py
```

The script prints its progress, writes up to 20 records to `sample_output.json` in the current directory, and prints the first record to the console.

## Example output

A real excerpt of `sample_output.json` from an actual run of this script (one FDA record, one EMA record - field names match the production actor's real dataset schema: `recordSource`, `jurisdiction`, `recipient_or_defendant_name`, `category_or_type`, `status_or_estado`, `reference_number`, `reason_for_recall`, `active_substances`):

```json
[
  {
    "recordSource": "fda_enforcement",
    "jurisdiction": "US",
    "scraped_at": "2026-09-10T14:58:56.710890+00:00",
    "recipient_or_defendant_name": "ACCORD HEALTHCARE, INC.",
    "category_or_type": "Drugs",
    "status_or_estado": "Ongoing",
    "reference_number": "D-0785-2026",
    "classification": "Class II",
    "reason_for_recall": "Subpotent Drug",
    "source_url": "https://api.fda.gov/drug/enforcement.json"
  },
  {
    "recordSource": "ema_dhpc",
    "jurisdiction": "EU",
    "scraped_at": "2026-09-10T14:58:56.710890+00:00",
    "recipient_or_defendant_name": "Jentadueto",
    "category_or_type": "Quality defect",
    "status_or_estado": null,
    "reference_number": null,
    "active_substances": "linagliptin;metformin hydrochloride",
    "source_url": "https://www.ema.europa.eu/en/medicines/dhpc/jentadueto"
  }
]
```

(Both feeds are live and change over time - openFDA adds new recalls and EMA publishes new DHPCs regularly, so running the script again will return whatever is currently newest, not necessarily these exact two records.)

## What this doesn't do

This stub is intentionally simple. It does **not** include:

- **Scheduling.** It runs once when you invoke `python main.py` and exits. There is no cron, no recurring trigger, no "run every N hours."
- **Delta / change-tracking.** Every run is a fresh, independent snapshot. It does not remember what it fetched last time, so it cannot tell you what's new since your last pull, or flag when an FDA recall's `status` flips from `Ongoing` to `Terminated`, or when an EMA `regulatory_outcome` updates.
- **Retries or backoff.** If a request to openFDA or EMA fails (rate limit, timeout, server error), the script prints the error for that source and moves on. It does not retry, and it does not honor rate-limit or `Retry-After` guidance from either regulator.
- **Dead-letter handling.** There is no mechanism for capturing, queuing, or replaying failed requests.

## Production version

For scheduled runs, delta/change-tracking, and reliability guarantees, see the production actor: https://apify.com/stefano_seggio/actor-22-drug-safety-recalls-monitor
