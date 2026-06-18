# MVP Documentation — Maison Lumière "P2P"
*Ironhack Final Project · stretch deliverable · `mvp/mvp_documentation.md`*

> The working, deployed application. The same build is the project's POC (`poc/poc_documentation.md`); this document is the production-oriented technical view. **Source + commit history:** https://github.com/thibauddelaye-sys/P2P-Final-Project · **Live:** https://p2p-inventory-production.up.railway.app

---

## 1. Architecture overview

```
                         ┌──────────────────────── Railway service (one) ────────────────────────┐
  Supplier ──e-mail──►   │  api/email_intake.py        api/main.py (FastAPI)        web/index.html │
  documents             │  (IMAP, unread only)  ──►   routes:                  ──►  cockpit SPA    │
  (PDF/JPG/PNG)          │                              /api/documents  (capture, group, match)    │
        │                │  manual upload ──────────►   /api/accounting (journal proposals)         │
        │                │                              /api/receipts   (goods receipt, dispute)    │
        │                │            ┌───────────────  /api/email      (send dispute)              │
        │                │            │                 /api/extract    (LLM read)                  │
        │                │            ▼                                                             │
        │                │   api/documents.py ──► extract_document()  ──►  Anthropic Claude (API)   │
        │                │        │   │                  │ (traced)                                 │
        │                │        │   │                  └──────────────►  LangSmith (tracing)      │
        │                │        │   └── dispute PDF (PyMuPDF) + photo ──►  Resend (HTTPS e-mail)   │
        │                │        ▼                                                                 │
        │                │   /store volume:  store.json (state) · files/ (raw docs + photos)        │
        │                │        ▲                                                                 │
        │                │   data/: suppliers.json · gl_lookups(.local).json · account_keywords.json│
        │                └──────────────────────────────────────────────────────────────────────-─┘
        └─► dedicated Gmail mailbox (maisonlumiere.invoices@…)
```

**Layers:** an IMAP intake + manual upload feed a document store on a persistent volume; an LLM extraction step (Claude, traced to LangSmith) returns structured JSON; grouping/dedup + GL-learned imputation produce accounting proposals and a 3-way match; goods-receipt and a PyMuPDF dispute-PDF generator feed an HTTPS e-mail send (Resend). One FastAPI service serves both the API and the cockpit.

---

## 2. Setup & installation

**Prerequisites:** Python 3.13, an Anthropic API key. (Optional: a Gmail mailbox + app password for e-mail capture; a Resend API key for sending; LangSmith keys for tracing.)

```bash
git clone https://github.com/thibauddelaye-sys/P2P-Final-Project
cd P2P-Final-Project
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys (never commit .env)
```

**Environment variables**

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | LLM document extraction |
| `EXTRACT_MODEL` | optional | Default `claude-haiku-4-5`; swap to Sonnet for tough scans |
| `STORE_DIR` | prod | Set to `/store` and attach a Railway volume to persist documents |
| `IMAP_USER` / `IMAP_PASSWORD` | optional | E-mail capture (Google app password) |
| `RESEND_API_KEY` / `RESEND_FROM` | optional | Send dispute e-mails over HTTPS |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` / `LANGSMITH_ENDPOINT` | optional | Extraction tracing (use the EU endpoint to keep traces in-region) |

---

## 3. How to run it

**Locally:**
```bash
uvicorn api.main:app --reload --port 8100
# open http://localhost:8100
```
**On Railway:** new service from the repo (the `Procfile` runs uvicorn on `$PORT`); set the env vars above; attach a volume at `/store`. The cockpit is served at `/`.

**Walk-through:** Reception → drop a sample invoice → see the proposed entry → 3-Way Match → review the discrepancy flags → Goods Receipt → record a delivery, attach a photo, draft/send a dispute → Accounting → edit lines and export the CSV journal.

---

## 4. Basic error handling (fails gracefully)

- **LLM JSON:** `json-repair` recovers malformed model output; extraction never crashes the request.
- **Long invoices:** `max_tokens` sized for multi-line documents; the model client is created lazily per call.
- **E-mail sending:** tries Resend (HTTPS) and falls back to SMTP; outbound-SMTP-blocked and non-ASCII sender-name cases are handled with clear errors and RFC 2047 encoding.
- **Tracing:** if LangSmith is absent or misconfigured, the app runs unchanged (no-op wrappers).
- **Persistence:** documents are re-hydrated from the volume at startup; missing keys return cleanly.

---

## 5. Known limitations & what production would need

| Area | MVP today | Production |
|---|---|---|
| Tenancy / auth | Single instance, no accounts | Multi-tenant, authentication, role-based access, full audit logging |
| Data protection | Synthetic data; secrets & real GL git-ignored | DPAs with all processors, EU-region processing, retention/purge policy, DSAR workflow (see `compliance/`) |
| Accuracy | Strong on the test set; degraded scans can mis-read | Confidence-threshold routing, accuracy-drift monitoring, per-client backtesting |
| Tracing privacy | Raw bytes redacted from the top-level trace | Also redact the trace **output**, or set the EU endpoint / disable tracing in prod |
| E-mail | Free Resend tier (`onboarding@resend.dev`) | Verified sending domain + deliverability monitoring |
| Resilience | Single region; basic retries | Rate-limit handling, queueing, regional redundancy, alerting |
| Inventory | Goods receipt + 3-way match | Full SKU-level stock movements + auto-reorder (roadmap B) |

---

## 6. How it extends the POC

The POC and this MVP are the **same artifact** — the POC *matured into* the MVP. A bare proof of concept would only demonstrate "an LLM can read an invoice." This build goes well beyond that, into a usable back-office tool:

- **From single-invoice extraction → a full document workflow:** multi-source capture (e-mail + upload), de-duplication by identity, and PO-based grouping.
- **From "read a field" → financial logic:** GL-learned account/VAT imputation from the hotel's real chart of accounts, a quantified 3-way match, and a goods-receipt control step.
- **From a demo → operational outputs:** a balanced GL-ready CSV journal, stock-in export, and a bilingual supplier dispute e-mail with a generated PDF constat + photo.
- **From ephemeral → persistent & observable:** a Railway-volume document store that survives restarts, plus LangSmith tracing of the AI step.
- **From happy-path → graceful failure:** JSON repair, e-mail fallbacks, and no-op tracing when unconfigured.

In short: the POC proves the **capability**; the MVP proves the **workflow, the financial correctness, and the deployability** around it.
