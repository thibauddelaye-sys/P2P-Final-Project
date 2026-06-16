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

## Email capture (Reception → "Check inbox")

Suppliers email invoices to a dedicated mailbox; the tool reads new ones with the same AI flow.

- Endpoint: `POST /api/email/poll` — pulls **unseen** attachments (PDF/JPG/PNG), runs each through the LLM extraction, returns the proposed entries. Marks them read so they aren't reprocessed.
- Module: `api/email_intake.py` (IMAP fetch, standard library only).
- Config (environment variables, **never commit secrets**):
  - `IMAP_HOST` (optional, default `imap.gmail.com`)
  - `IMAP_USER` — the dedicated mailbox address
  - `IMAP_PASSWORD` — a Google **app password** (requires 2-Step Verification; not the account password)

On the Reception page, click **Check inbox**: new emails are read and shown as proposed entries. The simulated list remains as a fallback when no mailbox is configured.

> Test with **synthetic** invoices only — real supplier documents contain third-party PII (names, IBAN, VAT) and must not be sent to the API or committed.

## Documents page — capture everything, match automatically

Beyond the single-invoice Reception flow, the **Documents** page captures *all* document types
emailed to the mailbox (purchase orders, delivery notes, invoices), classifies and extracts each
with the LLM, and **groups them automatically by purchase-order number**. A complete set
(PO + delivery note + invoice) is run through a 3-way match; exceptions (e.g. a price billed above
what was ordered) are flagged with the € caught before payment. Click any document to inspect what
the AI read.

Endpoints: `POST /api/documents/poll` (capture from mailbox), `GET /api/documents` (grouped view),
`POST /api/documents/sample` (load a demo set — works with no mailbox/API key), `DELETE /api/documents`.
State is in-memory (single-worker demo); re-polling re-reads and de-dupes, so it is safe to repeat.
