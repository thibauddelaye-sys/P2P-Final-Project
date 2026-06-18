# Maison Lumière — "P2P" AP & Inventory Tool (working MVP)

An AI-assisted **accounts-payable + inventory** application for an independent 5★ hotel. It reads supplier documents with an LLM, proposes the accounting entry, runs a 3-way match, controls goods receipt, and drafts supplier dispute e-mails — **AI reads, humans decide.**

> **Demo system: synthetic data, real logic, real AI.** No real company or personal data is committed or sent to any API.

## 🚀 Live

- **Cockpit (live demo):** https://p2p-inventory-production.up.railway.app
- **Application repo (source + commit history):** https://github.com/thibauddelaye-sys/P2P-Final-Project

## What it does

The cockpit has four pages, one per step of the AP workflow:

- **Reception** — capture a document (drop a PDF/JPG/PNG, or pull new ones from the mailbox via *Check inbox*). An LLM reads it and proposes the accounting entry. Documents are de-duplicated and grouped by PO reference. *(AI reads, humans decide.)*
- **3-Way Match** — every invoice line checked against ordered vs received; flags overbilling, price variance and short delivery, and quantifies the € caught before payment. Manual re-grouping and a cursor magnifier are built in.
- **Goods Receipt** — record what physically arrived vs the delivery note; surface discrepancies; attach an evidence photo; draft and send a bilingual dispute e-mail (PDF constat + photo attached).
- **Accounting** — review/edit the proposed double-entry journal line by line (account · VAT · analytical allocation), then export a balanced, GL-ready CSV journal (ACH format).

## Run locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # required for AI invoice reading
# optional — e-mail capture (Reception → Check inbox):
#   IMAP_USER=...   IMAP_PASSWORD=...(Google app password)
# optional — sending dispute e-mails:
#   RESEND_API_KEY=...   RESEND_FROM="Maison Lumière <onboarding@resend.dev>"
uvicorn api.main:app --reload --port 8100
# open http://localhost:8100
```

> Test with **synthetic** invoices only — real supplier documents contain third-party PII and must not be sent to the API or committed.

## Deploy (Railway — one service)

- New service from the application repo; the `Procfile` handles startup.
- Set `ANTHROPIC_API_KEY` (and optionally the IMAP / Resend / LangSmith variables).
- Set `STORE_DIR=/store` and attach a Railway **volume** at `/store` so captured documents persist across restarts.
- The web cockpit is served by the same service at `/`.

## Structure (application repo)

```
api/main.py          FastAPI: extraction · 3-way match · accounting · goods receipt · e-mail · exports; serves the UI
api/documents.py     document store, LLM extraction, grouping/dedup, imputation, dispute PDF, Resend/SMTP send
api/email_intake.py  IMAP fetch of unread invoice attachments (standard library only)
web/index.html       the cockpit (Reception · 3-Way Match · Goods Receipt · Accounting)
data/                suppliers.json (11 fictional suppliers) · gl_lookups.json (generic/pseudonymised) · account_keywords.json
build_gl_lookups.py  builds gl_lookups.local.json from a real GL (local only; git-ignored)
```

## Data governance

- **Synthetic suppliers** and **generic/pseudonymised** GL labels are the only data committed.
- A real chart of accounts, if used, lives in `data/gl_lookups.local.json`, which is **git-ignored** and used preferentially over the public demo lookup.
- Secrets live in environment variables and are **never committed** (`.env` is git-ignored).

See `compliance/` (in the Final-Project repo) for the EU AI Act and GDPR assessments.
