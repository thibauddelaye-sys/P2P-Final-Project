# Final Project — Maison Lumière "P2P"
### AI-Assisted Accounts-Payable & Inventory Automation for Luxury Hospitality
*Ironhack — AI Consulting & Integration · Thibaud Delaye*

A working AI tool that reads supplier invoices, proposes accounting entries, runs a 3-way match, controls goods receipt and drafts supplier dispute e-mails for an independent 5★ hotel — **AI reads, humans decide.** This repository holds the **deliverables**; the application source lives in a separate repo (linked below).

---

## 📁 File map

```
final-project-thibaud-delaye/
├── README.md                         ← this file map
├── use_case_definition.md            #1 — business problem, profile, solution, stakeholders, success criteria, scope
├── poc/
│   ├── poc_documentation.md          #2 — the (code-based) proof of concept: tools, steps, AI capability, limits, how to run
│   └── poc_screenshots/              #2 — [ADD: annotated screenshots of each page]
├── roi_risk_assessment.md            #3 — costs, business value, ROI (12 & 36 mo), assumptions, break-even, 9-risk matrix
├── compliance/
│   ├── eu_ai_act_compliance.md       #4 — classification (limited risk/transparency), reasoning, obligations, conformity summary, tech-doc outline
│   └── gdpr_documentation.md         #5 — data flow map, processing register, DPIA, data-subject rights, third-party transfers
├── strategic_plan.md                 #6 — deployment phases, timeline, go-to-market, stakeholder comms, KPIs, commercialisation
├── presentation.pdf / .pptx          #7 — [TO BUILD: slide deck for Week 9 Day 5]
└── mvp/                              #8 (stretch)
    ├── README.md                     working-MVP overview (also usable to refresh the application repo's README)
    └── mvp_documentation.md          architecture, setup, run, error handling, limitations, how it extends the POC
```

**Application source (the working MVP / POC):** https://github.com/thibauddelaye-sys/P2P-Final-Project
**Live demo:** https://p2p-inventory-production.up.railway.app

---

## ✅ Submission checklist

**Core**
- [x] `use_case_definition.md`
- [x] `poc/poc_documentation.md` — _add demo-recording link + screenshots_
- [x] `roi_risk_assessment.md`
- [x] `compliance/eu_ai_act_compliance.md`
- [x] `compliance/gdpr_documentation.md`
- [x] `strategic_plan.md`
- [ ] `presentation.[pdf/pptx]` — **to build** (deck synthesising the above)

**Stretch**
- [x] `mvp/mvp_documentation.md` + `mvp/README.md`
- [x] GitHub repository link → the application repo above (organised code, `requirements.txt`, `.env.example`, commit history)

**Still to add by hand**
1. **Demo recording (2–5 min)** — paste the link into `poc/poc_documentation.md`.
2. **POC screenshots** — drop annotated images into `poc/poc_screenshots/`.
3. **Presentation deck** — `presentation.pptx` (next deliverable).
4. *(Optional)* refresh the application repo's `README.md` using `mvp/README.md` (the current one still mentions removed Stock/Scan pages).

---

> All operational KPIs are a **modelled pilot projection**; market-evidence figures are **real and cited** (mostly directional vendor/US benchmarks, flagged as such). Demo runs on **synthetic data** — no real company or personal data. Compliance documents are first-pass assessments, **not legal opinions**.
