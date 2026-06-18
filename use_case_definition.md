# Use Case Definition — Maison Lumière "P2P"
### AI-Assisted Accounts-Payable & Inventory Automation for Luxury Hospitality
*Ironhack Final Project · `use_case_definition.md`*

> Built on the use-case discovery and market research conducted in Project 5 (Module 5 — AI Strategy & Business Impact). Industry benchmarks below are **real and cited but directional** (mostly US/global); client-specific figures are flagged for validation. The operational KPIs are a **modelled pilot projection**, not live results.

---

## 1. Business problem statement

Independent luxury hotels are caught in a structural squeeze: the post-pandemic cost base has reset higher and now grows faster than room revenue (gross-operating-profit margins declining through 2025, per HVS and Hospitality Investor), while the sector runs on people who are hard to keep (hospitality turnover commonly cited at 70–80%/yr; replacing one employee ≈ €4,400–4,700+). Cutting labour to protect margin therefore backfires — it worsens the very turnover and service-quality problem that justifies a luxury rate.

Sitting on top of that lean team is a large, quiet, manual cost: **accounts-payable**. Manual invoice processing costs ≈ €11–14 per invoice and ≈ 14.6 days cycle time, ≈ 68% of teams still key invoices by hand, and manual error rates run high — all compressible by automation to ≈ €2–5, ≈ 3–5 days, and near-zero straight-through error.

**The problem, in one line:** every hour and euro spent keying supplier invoices is an hour and euro *not* spent on the guest experience — and it burns out the small finance team the hotel depends on.

**For whom:** the lean back-office finance team of an independent 5★ hotel (AP clerk, accountant, cost controller) and the owner/CFO who must protect margin without cutting service.

---

## 2. Company profile

| Attribute | Value |
|---|---|
| **Fictional client** | **Maison Lumière** — an independent five-star hotel; the **owner/CEO** is evidence-driven ("anti-hype, not anti-AI") |
| **Industry** | Luxury hospitality — independent & small-group 5★ hotels |
| **Company size** | **SME** — single property to small group, ~80–250 employees |
| **Geography / context** | Luxembourg / EU (EU data-protection and AI-Act regime applies) |
| **Current operational state** | Lean finance team keying supplier invoices manually; slow month-end close; no AP automation; structurally high staff turnover; the EU e-invoicing wave (ViDA / Luxembourg B2B mandate ~2028–29) is approaching, making structured invoices the near-future norm |

Large chains centralise finance in shared-service centres; independents and small groups do not — so the back-office burden, and therefore the ROI of automating it, is **concentrated and visible** on one small team. This is what makes the case concrete rather than generic.

---

## 3. Proposed AI solution

**What the AI does (end to end):**
1. **Captures** supplier documents — invoices, purchase orders, delivery notes — pulled from a dedicated mailbox or dropped in manually (PDF / image).
2. **Reads & extracts** each document with a large language model (supplier, invoice number, dates, line items, amounts, VAT) — no manual keying.
3. **Proposes the accounting entry** — account, VAT treatment, and analytical/cost-centre allocation — learned from the hotel's own chart of accounts.
4. **Runs a 3-way match** — checks ordered vs received vs billed for every line, and **quantifies in € the overbilling, price variances and short deliveries caught before payment.**
5. **Drafts a dispute email** to the supplier when a discrepancy is found.
6. **Hands the decision to a human** — a finance team member reviews, corrects and approves every proposed entry; nothing is posted, paid or sent autonomously.

**Type of AI system:** primarily **process automation** of the AP/back-office workflow, built on **generative AI** for document understanding/extraction, with a light **recommendation** component (GL-account suggestion). It is explicitly **not** a system that classifies, scores or makes decisions about *people*.

**Core design principle:** *AI reads, humans decide* — the human remains accountable for every posted entry and every sent message.

**Technology (the working MVP):** Anthropic Claude (via API) for extraction; a FastAPI application with a web cockpit (Reception · 3-Way Match · Goods Receipt · Accounting), deployed on Railway, with email capture and CSV/journal export.

---

## 4. Key stakeholders

| Stakeholder | Role re: the system | Need / pain today |
|---|---|---|
| **CEO / Owner** | **Decides** (sponsors the investment) | Protect margin without damaging service; will not "burn budget on hype" — needs evidence |
| **CFO / Finance Director** | **Decides / owns** the process | Slow, firefighting month-end close; limited headcount, can't simply hire |
| **Accountant / AP clerk** | **Primary user** | Manual, repetitive, error-prone invoice keying; volume spikes overwhelm a small team |
| **Cost controller** | **User** | Reconciling cost invoices (F&B, consumables) against deliveries is manual and lagging |
| **General Manager** | **Affected** | Wants skilled staff focused on guests, not paperwork |
| **Front-line / finance staff** | **Affected** (the "passion") | Admin overload feeds fatigue and turnover |
| **Suppliers** | **Affected** (receive matched/disputed billing) | Faster, more accurate dispute resolution |

**Key insight:** the same lean team is both the *bottleneck* (slow close, error risk) and the *flight risk* (burnout). Relieving it addresses **cost and retention at once**.

---

## 5. Success criteria (measurable)

*The brief requires at least two; four are defined so the pilot can baseline and pick the most credible. Targets are a modelled pilot projection (Jun–Nov 2026) to be confirmed against the client's real volume.*

| # | Metric | Definition | Modelled target (to validate) |
|---|---|---|---|
| **SC1** | **Touchless / straight-through rate** | % of invoices the AI proposes correctly with **no** human correction | Ramps **~58% → ~92%** across the pilot as the model learns this hotel's formats |
| **SC2** | **Handling time per invoice** | Minutes from receipt to approved entry vs the manual baseline | **~15 min → ~3 min** |
| **SC3** | **Finance hours returned** | Hours freed for higher-value work / overtime not worked | **≈ 984 h/yr** at the hotel's real volume |
| **SC4** | **Accuracy / exception rate** | Error rate on posted entries vs manual baseline | Account accuracy stabilising **~94%** |

(These feed directly into the ROI model: ≈ €42k/yr saved on the AP scope alone, roughly breakeven in year 1. See `roi_risk_assessment.md`.)

---

## 6. Out-of-scope boundaries

To keep the case honest, the risk low, and the human accountable, the system explicitly does **not**:

- **post any accounting entry autonomously** — a human approves every entry (this is a hard boundary, not a setting);
- **touch payroll, HR, or any worker-management / performance decision** — the "who captured / who counted" field is an **audit trail, not an evaluation** (this boundary is what keeps the system out of the EU AI Act's high-risk *employment* category);
- **face the guest or alter the guest experience** in any way;
- **assess the creditworthiness of, or score, any individual** (it processes the hotel's own payables, not decisions about people);
- **automate full inventory / SKU-level stock movements or autonomous reordering** — the tool handles goods-receipt control and 3-way matching, but item-level stock automation and auto-reorder are a **deferred roadmap phase**, not this scope;
- **send dispute emails autonomously** — every supplier message is reviewed and sent by a person.

> **Scope note vs Project 5.** Project 5's *pilot* scoped only invoice→entry (use case "A"). The Final-Project tool delivered here goes further — it also implements **3-way match against POs/receipts and cost-control invoices** (part of use case "B") and **goods-receipt control** — while still deferring full SKU-level stock automation. The boundaries above reflect what is **actually built**.

---

*Companion deliverables: `roi_risk_assessment.md`, `eu_ai_act_compliance.md`, `gdpr_documentation.md`, `strategic_plan.md`, `poc/poc_documentation.md`, `mvp/mvp_documentation.md`.*
