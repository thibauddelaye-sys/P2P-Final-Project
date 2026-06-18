# Strategic Deployment & Commercialisation Plan — Maison Lumière "P2P"
*Ironhack Final Project · `strategic_plan.md`*

> From the working build to a live, commercially viable offering. Grounded in the Project 5 solution proposal, implementation plan and cost model. The recommendation is deliberately **falsifiable**: a real go/no-go gate after the pilot.

---

## 1. Deployment phases

| Phase | Name | State / goal | Scope |
|---|---|---|---|
| **Phase 1** | **POC (current state)** | Working application, deployed, proving the AI capability end to end | Capture → extract → propose entry → 3-way match → goods receipt → dispute e-mail → export, on synthetic data |
| **Phase 2** | **Pilot (limited rollout, validation)** | Turn directional benchmarks into evidence on *this hotel's* real invoices; controlled scope, human on every entry | G&A supplier invoices, real vendor master + COA, the 4 success metrics; preceded by a 1–2 wk **Preparation** step (volumes, DPAs, EU processing, confidence threshold) |
| 🚦 | **Decision gate** (end of pilot) | Falsifiable go/no-go | **Touchless ≥ 65% AND accuracy ≥ 90% at real volume → proceed.** Miss narrowly → tune/extend. Miss badly or volume too thin → stop, learning banked |
| **Phase 3** | **Full deployment (rollout & hardening)** | Scale to all G&A vendors; productionise | Monitoring/alerting on accuracy drift, the EU AI Act file + DPIA finalised, Peppol/e-invoice channel connected |
| **Phase 4** | **Scale / expansion (roadmap)** | Extend value pools; multi-property / multi-client | **B:** cost-control invoices → P&L + SKU-level stock movements. **C:** automated monthly P&L + AI variance commentary. Then replicate to additional properties/hotels |

---

## 2. Timeline & milestones

| Phase | Duration | Key milestones |
|---|---|---|
| **0 · Preparation** | 1–2 weeks | Real volumes confirmed · DPAs + EU-region processing · vendor master & COA loaded · confidence threshold set |
| **1 · Pilot** | 10 weeks | Flow live · weekly accuracy backtest · team trained · 4 success metrics tracked |
| 🚦 **Decision gate** | end of wk ~12 | Touchless ≥ 65% & accuracy ≥ 90% at real volume → go |
| **2 · Rollout & hardening** | 8–10 weeks | All G&A vendors · monitoring/alerting · DPIA + AI-Act file · Peppol/e-invoice channel |
| **3 · Extend (B, C)** | later | Cost-control + stock; automated P&L reporting |

```
Wk:  0────2────────────────12 (gate)────────────22 ───────►  scale
     │Prep │      Pilot      │     Rollout/harden │   Extend / replicate
```

**Total to a scaled, hardened single-hotel solution: ~5–6 months** from kickoff, with a real decision point at ~week 12 costing only the ~€20k pilot to reach.

**Regulatory tailwind (timing the e-invoicing wave):**
```
2025 ViDA adopted ─ 2026 LU law / Belgium B2B ─ 2027 France B2B ─ 2028–29 LU domestic B2B ─ 2030 EU intra-B2B
        │                    │                                          │
     Phase 0/1 now      Phase 2 (e-invoicing ready)            already compliant & ahead
```
Building now means the hotel meets the 2028–29 Luxembourg obligation from a position of strength, not a scramble.

---

## 3. Go-to-market strategy

**Target buyers / customers.** Independent and small-group **5★ hotels (SME, ~80–250 employees)** in Luxembourg and the wider EU, where finance is **not** centralised in a shared-service centre — so the back-office pain and the ROI are concentrated on one lean team. Economic buyer: **owner/CEO** and **CFO/Finance Director**; champion/user: **AP clerk / cost controller**.

**Sales channel.**
- **Phase 2–3:** **direct, consultative sale** — the pilot *is* the sales motion (a low-risk, evidence-generating paid engagement). Best fit for a trust-sensitive "AI doing the books" decision.
- **Phase 4:** **partner channel** — hospitality accounting firms, PMS/ERP integrators, and hospitality groups; optionally a **marketplace** listing (PMS/accounting app stores) once the product is multi-tenant.

**Pricing model.** A **hybrid land-and-expand**:
- **Pilot fee** — ~€20k fixed (de-risks the buyer; covers adaptation + supervision).
- **Subscription (run)** — ~€13k/yr per property (tooling + support + tuning), optionally tiered by invoice volume, or a **per-invoice** micro-fee for variable usage.
- **Expansion** — modules B (stock) and C (reporting) priced as add-ons.
This mirrors the cost model and keeps pricing **anchored to delivered savings** (€42k–€93.5k/yr) so the ROI story is always intact.

**Key differentiator vs existing alternatives.** Generic AP-automation tools exist; this offering is **vertical and EU-native**:
- **Luxury-hospitality specific** — USALI allocation, F&B/consumables cost-control, hotel supplier mix.
- **EU-compliant by design** — AI Act limited-risk posture, GDPR documentation, e-invoicing/Peppol-ready ahead of the LU mandate.
- **Human-in-the-loop as a feature, not a caveat** — "second set of eyes" is the trust story the sector explicitly wants (Inn-Flow's back-office survey).
- **Honest, falsifiable business case** — sold on a pilot gate, not a promise.

---

## 4. Stakeholder communication plan

| Stakeholder group | What they need to know | Who communicates | When |
|---|---|---|---|
| **Owner / CEO** | The case, the cost, the falsifiable gate, the margin + retention upside | Project lead / consultant | Kickoff; gate decision; quarterly |
| **CFO / Finance Director** | Process changes, controls, the close impact, compliance posture | Project lead + finance owner | Weekly during pilot |
| **AP clerk / cost controller (users)** | "Second set of eyes", no headcount cuts, how to review/correct, that they stay accountable | Trainer / change lead | Training (Phase 0/1); ongoing |
| **General Manager** | That service-facing staff are unaffected; team time is freed, not cut | Project lead | Kickoff; rollout |
| **DPO / legal counsel** | Classification, DPIA, DPAs, transfers, retention | Compliance owner | Phase 0; before any real data; before scaling |
| **Suppliers** | That dispute e-mails are AI-assisted but human-reviewed (Art. 50 line) | Automated footer + finance team | On first AI-assisted e-mail |

Communication principle (sector-tuned): **"AI assists, humans decide" + no headcount cuts** — this is what defuses change-resistance and the trust gap the data shows (trust 6.6 vs reliance 4.7).

---

## 5. KPIs per phase

| Phase | KPIs |
|---|---|
| **1 · POC** | AI capability demonstrated end-to-end; extraction works across the supplier-template mix and degraded scans |
| **2 · Pilot** | **Touchless rate** (→ ≥65%), **account accuracy** (→ ≥90%), **handling time/invoice** (→ ≤5 min), **finance hours returned** (positive & material) — all at real volume |
| **3 · Full** | Touchless ramping toward ~88%, accuracy ~94%, accuracy-drift alerts clean, **€ saved/yr realised** vs the €42k model, DPIA/AI-Act file complete |
| **4 · Scale** | Modules B/C value pools realised (toward €93.5k net), # properties/clients live, gross-margin per deployment, churn/retention |

---

## 6. Commercialisation model — and why

**Model: a productised vertical service — "internal tool → boutique SaaS-with-onboarding".**

The build is offered as a **product with a consultative onboarding**, not as pure custom consulting and not (yet) as a self-serve SaaS:
- **Why not pure internal tool?** It solves a problem common to a whole segment (independent 5★ hotels); the marginal cost of serving the next hotel is low once multi-tenant — there is a real product opportunity, not a one-off.
- **Why not pure self-serve SaaS (day one)?** The decision is trust-sensitive and each hotel needs adaptation (supplier formats, COA, VAT). A **paid pilot + subscription** wins trust and funds the adaptation; self-serve can come later for smaller properties.
- **Why not pure consulting?** Consulting doesn't scale and doesn't capture recurring value; the subscription does, and keeps incentives aligned with the savings delivered.

**Path:** prove it as Maison Lumière's internal tool (Phases 1–3) → package the repeatable parts (extraction, matching, COA-mapping, compliance kit) into a multi-tenant product → sell direct, then via partners, to the next independent 5★ hotels (Phase 4). The EU-compliance kit and the e-invoicing readiness are part of the product, not an afterthought — they are a moat in this regulated, trust-sensitive segment.

---

*Companion deliverables: `use_case_definition.md`, `roi_risk_assessment.md`, `compliance/`, `mvp/mvp_documentation.md`.*
