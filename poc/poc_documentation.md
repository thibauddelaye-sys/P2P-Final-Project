# POC Documentation — Maison Lumière "P2P"
*Ironhack Final Project · `poc/poc_documentation.md`*

> **Note on POC format.** This project's proof of concept is a **working code-based application** rather than a no-code/low-code workflow. The same build is submitted as the optional **stretch MVP** — the POC matured directly into the MVP, which is itself the strongest evidence that the AI capability works end to end on real document formats. Full architecture and run instructions are in `mvp/mvp_documentation.md`; this file gives the POC-level view (what it proves, how to see it run, its limits).

---

## 1. Tools used — and why

| Tool | Role | Why this choice |
|---|---|---|
| **Anthropic Claude (Haiku 4.5)** via API | Reads each supplier document and returns structured JSON | LLM-based extraction handles **varied, messy invoice layouts** far better than template OCR — exactly what an independent hotel's heterogeneous supplier base needs. `EXTRACT_MODEL` is swappable to Sonnet for tougher scans. |
| **FastAPI** (Python) | Backend: extraction, 3-way match, accounting imputation, goods-receipt, e-mail, exports | Lightweight, async, self-documenting (`/docs`); fast to build and deploy. |
| **Web cockpit** (HTML/JS + Chart-style UI) | The finance-team interface (Reception · 3-Way Match · Goods Receipt · Accounting) | One screen per step of the AP workflow; no build chain needed. |
| **Railway** | Hosting + a persistent volume (`/store`) | One-service deploy from GitHub; volume keeps captured documents across restarts. |
| **Gmail / IMAP** | A dedicated mailbox suppliers send invoices to | Lets the tool ingest invoices the way they really arrive — by e-mail — using only the Python standard library. |
| **Resend** (HTTPS e-mail API) | Sends the supplier dispute e-mail (with PDF + photo) | Railway blocks outbound SMTP on the hosting tier; Resend sends over HTTPS. |
| **LangSmith** | Tracing/observability of the extraction step | Makes the AI step debuggable (latency, failures) without logging raw document bytes. |
| **json-repair** | Hardens JSON parsing of the model output | Real-world LLM JSON is occasionally malformed; this recovers it gracefully. |

---

## 2. What the POC does — step by step

1. **Capture.** A supplier invoice, purchase order or delivery note enters the system — either pulled from the mailbox (*Reception → Check inbox*) or dropped in manually (PDF / JPG / PNG).
2. **Read & extract.** The document is sent to Claude, which returns structured data: supplier, document number, PO reference, dates, line items, quantities, amounts, VAT, total.
3. **De-duplicate & group.** Documents are de-duplicated by identity and grouped by PO reference so the order, the delivery and the invoice line up automatically.
4. **Propose the accounting entry.** Using the hotel's own chart of accounts, the tool proposes the GL account, VAT treatment and analytical allocation — line by line, editable.
5. **3-way match.** For every line it compares **ordered vs received vs billed** and flags overbilling, price variance and short delivery, quantifying the € caught before payment.
6. **Goods receipt.** A staff member records what physically arrived; discrepancies vs the delivery note are surfaced, with an optional evidence photo.
7. **Dispute (if needed).** The tool drafts a dispute e-mail (FR/EN) to the supplier and attaches a generated PDF constat + the photo; a human reviews and sends it.
8. **Export.** Validated entries export as a GL-ready, balanced CSV journal (ACH format); stock-in exports as CSV.

**Throughout: AI reads and proposes, a human reviews and decides.** Nothing is posted, paid or sent autonomously.

---

## 3. What AI capability is demonstrated

- **Document understanding / information extraction** from heterogeneous, real-world invoice layouts (multiple supplier templates, multi-page documents, and deliberately degraded scans) — the core, non-trivial capability.
- **Schema-constrained generation** — the model returns a strict JSON schema, made robust with repair-on-failure.
- **Light recommendation** — mapping each extracted line to the correct GL account + VAT treatment, learned from the hotel's real (pseudonymised) chart of accounts.
- **Generative drafting** — producing a context-aware bilingual supplier dispute e-mail from the matched discrepancy.

The POC proves the decisive question no benchmark can answer: **can the model read *this* kind of supplier mix accurately enough to be useful, with a human on every entry?**

---

## 4. Known limitations of the POC vs a production system

| Area | POC today | Production would need |
|---|---|---|
| **Data** | Synthetic suppliers + pseudonymised/generic GL; real employer data only ever local (git-ignored) | Real client data under a signed data-processing agreement with each vendor |
| **Compliance** | Classification + DPIA documented as Final-Project deliverables | DPAs, EU-region processing, retention/purge policy, data-subject-rights workflow (see `compliance/`) |
| **Accuracy** | Strong on the test set; degraded scans can still mis-read | Confidence-threshold routing, accuracy-drift monitoring, per-client backtesting |
| **Tenancy / auth** | Single instance, no user accounts | Multi-tenant, authentication, role-based access, audit logging |
| **Resilience** | Lazy API client, retries on JSON; single region | Rate-limit handling, queueing, regional redundancy, alerting |
| **E-mail sending** | Free Resend tier (`onboarding@resend.dev`) | Verified sending domain, deliverability monitoring |
| **Retention** | Volume persists until manual delete/clear | Automated TTL on raw uploads + traces; long retention only for the legal accounting record |

---

## 5. How to reproduce / run it yourself

**Option A — see it live (no setup):** open the deployed cockpit at
`https://p2p-inventory-production.up.railway.app`.

**Option B — run locally** (from the application repo, `github.com/thibauddelaye-sys/P2P-Final-Project`):
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # required for the AI reading
# optional: IMAP_USER / IMAP_PASSWORD for e-mail capture
uvicorn api.main:app --reload --port 8100
# open http://localhost:8100
```
Then: drop a sample invoice on **Reception**, watch the proposed entry appear, open **3-Way Match** to see the discrepancy flags, and **Goods Receipt** to record a delivery. Sample/synthetic documents are used throughout — never send real supplier PII to the API.

---

## 6. Demo & evidence

- **Demo recording (2–5 min):** _[paste your screen-recording link here]_ — walk through Reception → 3-Way Match → Goods Receipt → dispute e-mail → CSV export.
- **Screenshots:** `poc/poc_screenshots/` — _[add annotated screenshots of each page]_.
- **Live system:** the deployed cockpit above (the same artifact submitted as the stretch MVP).

> Because the POC and the stretch MVP are the **same deployed application**, the strongest "evidence it runs" is the live system itself plus the recording.
