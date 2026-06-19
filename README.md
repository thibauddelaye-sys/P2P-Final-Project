# Maison Lumière — "P2P" · AI-Assisted AP & Inventory Tool + Final Project deliverables
*Ironhack — AI Consulting & Integration · Thibaud Delaye*

This repository is **both**:
1. the **working AI application** (source at the repository root, deployed and live), and
2. the **Ironhack Final Project deliverables** (the documents listed below).

> **Demo system: synthetic data, real logic, real AI.** No real company or personal data is committed or sent to any API. **AI reads, humans decide** — nothing is posted, paid or sent without a person approving it.

- **Live cockpit:** https://p2p-inventory-production.up.railway.app

---

## 📁 Repository map

**Final Project deliverables**
```
use_case_definition.md            #1 — problem, profile, solution, stakeholders, success criteria, scope
poc/poc_documentation.md          #2 — the (code-based) proof of concept: tools, steps, AI capability, limits, run
poc/poc_screenshots/              #2 — [ADD: annotated screenshots]
roi_risk_assessment.md            #3 — costs, ROI (12 & 36 mo), assumptions, break-even, 9-risk matrix
roi_risk_assessment.xlsx          #3 — same model as a live spreadsheet (formulas, risk matrix)
compliance/eu_ai_act_compliance.md  #4 — classification (limited risk/transparency), conformity summary, tech-doc outline
compliance/gdpr_documentation.md    #5 — data flow, processing register, DPIA, data-subject rights, transfers (+ EU-residency options)
strategic_plan.md                 #6 — deployment phases, timeline, go-to-market, KPIs, commercialisation
presentation.pdf / .pptx          #7 — slide deck, pf-05 structure (PDF preferred); demo + business case + compliance
mvp_documentation.md              #8 (stretch) — architecture, setup, run, limitations, how it extends the POC
```

**Working application (the MVP / POC source)**
```
api/main.py          FastAPI: extraction · 3-way match · accounting · goods receipt · e-mail · exports; serves the UI
api/documents.py     document store, LLM extraction, grouping/dedup, GL imputation, dispute PDF, Resend/SMTP send
api/email_intake.py  IMAP fetch of unread invoice attachments (standard library only)
web/index.html       the cockpit (Reception · 3-Way Match · Goods Receipt · Accounting)
data/                suppliers.json (11 fictional) · gl_lookups.json (generic/pseudonymised) · account_keywords.json
build_gl_lookups.py  builds gl_lookups.local.json from a real GL (local only; git-ignored)
requirements.txt · Procfile · .env.example
```

---

## What the app does

Four cockpit pages, one per step of the AP workflow:

- **Reception** — capture a document (drop a PDF/JPG/PNG, or pull new ones from the mailbox via *Check inbox*). An LLM reads it and proposes the accounting entry; documents are de-duplicated and grouped by PO reference.
- **3-Way Match** — every invoice line checked against ordered vs received; flags overbilling, price variance, short delivery; quantifies the € caught before payment.
- **Goods Receipt** — record what physically arrived vs the delivery note; surface discrepancies; attach an evidence photo; draft + send a bilingual dispute e-mail (PDF constat + photo).
- **Accounting** — review/edit the proposed double-entry journal line by line (account · VAT · analytical), then export a balanced, GL-ready CSV journal (ACH format).

## Run locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # required for AI invoice reading
# optional: IMAP_USER / IMAP_PASSWORD (Google app password) for e-mail capture
# optional: RESEND_API_KEY / RESEND_FROM for sending dispute e-mails
uvicorn api.main:app --reload --port 8100
# open http://localhost:8100
```

## Deploy (Railway — one service)

New service from this repo (the `Procfile` handles startup); set `ANTHROPIC_API_KEY`; set `STORE_DIR=/store` and attach a Railway **volume** at `/store` so captured documents persist. The cockpit is served at `/`.

## Data governance

Only **synthetic** suppliers and **generic/pseudonymised** GL labels are committed. A real chart of accounts, if used, lives in `data/gl_lookups.local.json`, which is **git-ignored** and used preferentially. Secrets live in environment variables (`.env` is git-ignored). See `compliance/` for the EU AI Act and GDPR assessments.

---

## ✅ Submission checklist

- [x] `use_case_definition.md`
- [x] `poc/poc_documentation.md` — _add demo-recording link + screenshots_
- [x] `roi_risk_assessment.md` + `roi_risk_assessment.xlsx`
- [x] `compliance/eu_ai_act_compliance.md` · `compliance/gdpr_documentation.md`
- [x] `strategic_plan.md`
- [x] `presentation.pdf` (+ `presentation.pptx`)
- [x] `mvp_documentation.md` + working MVP (this repo)

**To add by hand:** demo-recording link (in `poc/poc_documentation.md`) · screenshots (`poc/poc_screenshots/`).

> Operational KPIs are a **modelled pilot projection**; market figures are **real and cited** (directional vendor/US benchmarks, flagged). Compliance documents are first-pass assessments, **not legal opinions**.
