# Maison Lumière — AP & Stock Tool (functional prototype)

The **working tool** behind the Project 5 business case: an AI-assisted accounts-payable +
inventory system for an independent 5★ hotel. Where Project 5 *presents the case* for adopting
AI, this repo *is the tool* — it reads real invoices, proposes entries, runs a 3-way match,
tracks stock, and issues stock by barcode scan.

> Demo system: **synthetic data, real logic, real AI**. No real company/personal data.

## What it does
- **Reception** — drop an invoice (PDF/JPG/PNG) → an LLM reads it and proposes the accounting
  entry (account + VAT); optional match against a purchase order. *AI reads, humans decide.*
- **3-way match** — every invoice line checked vs ordered vs received; flags overbilling,
  price variance, short delivery; quantifies € caught before payment.
- **Stock & reorder** — live balances, reorder suggestions.
- **Scan** — phone camera scans a product barcode → issues stock → triggers reorder.

## Run locally
```bash
pip install -r requirements.txt
python generate_and_match.py            # builds data/ (seed 42)
export ANTHROPIC_API_KEY=sk-...         # for AI invoice reading
uvicorn api.main:app --reload --port 8100
# open http://localhost:8100
```

## Deploy (Railway — one service)
- New service from this repo; Procfile handles startup.
- Set env var **ANTHROPIC_API_KEY** (for the Reception page's AI reading).
- The web cockpit is served by the same service at `/`.

## Structure
```
api/main.py              FastAPI: match / stock / scan / extract (LLM) / serves the web UI
web/index.html           the cockpit (Reception · 3-Way Match · Stock · Scan)
scripts:                 generate_and_match.py  (synthetic data + 3-way match + stock ledger)
data/                    generated CSVs + printable barcodes
barcodes_print.html      printable demo barcodes to scan
```

Separate from the Project 5 deliverable repo by design. Foundation for the Ironhack Final Project.
