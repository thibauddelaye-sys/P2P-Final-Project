# ROI & Risk Assessment — Maison Lumière "P2P"
*Ironhack Final Project · `roi_risk_assessment.md`*

> **Figure provenance (read first).** Every number below is a **labelled planning estimate** built on the Project 5 cost model and sourced industry benchmarks. AP-automation benchmarks are mostly **vendor/US sources → directional**; client-specific volumes and rates must be confirmed (that is exactly what the pilot's decision gate is for). Currency: EUR. Loaded finance rate assumed **€45/h**.

---

## PART A — ROI Analysis

### A.1 Cost estimate — Upfront (one-off, 10-week pilot): **€20,000**

| Item | Estimate | What it covers |
|---|---|---|
| Discovery & process mapping | €3,000 | Map the current AP workflow, confirm volumes, vendor master & COA |
| Model adaptation & configuration | €7,000 | Extraction tuned to this hotel's supplier formats, account-mapping rules, VAT logic |
| Integration & deployment | €5,000 | Stand up capture → propose → validate → post; cockpit + reporting |
| Training & change management | €2,500 | Finance-team onboarding, "second set of eyes" framing |
| Pilot supervision & go/no-go evaluation | €2,500 | Weekly accuracy backtest, success-metric tracking, decision-gate report |

*(Development of the tool itself is sunk — the working build already exists. The €20k is the cost to put it into productive use at one hotel.)*

### A.2 Cost estimate — Ongoing (per year, after rollout): **€13,000 / yr**

| Item | Estimate |
|---|---|
| LLM usage — per-invoice extraction at full volume | €2,000 |
| Hosting & infrastructure | €2,000 |
| Support, monitoring & maintenance | €5,000 |
| Ongoing model tuning & quarterly re-adaptation | €4,000 |

### A.3 Business value estimate

**Committed (conservative) scope — AP invoice automation only**, at the hotel's assumed full volume (~420 invoices/month, ~78% touchless):

| Benefit | Value | Basis |
|---|---|---|
| Gross annual saving | **≈ €42,000** | Per-invoice handling €12 → €3.9 at €45/h, ~5,040 invoices/yr |
| Finance hours returned | ≈ 900 h/yr | Time not spent keying / firefighting |
| FTE freed | ≈ 0.6 | Labour pool ÷ €45/h ÷ 1,600 productive h |

**Expanded scope — the full tool actually built (AP + 3-way match + inventory)** unlocks four further **non-overlapping** pools (conservative, assumption-based):

| Value pool | €/yr | Kind |
|---|---|---|
| AP automation — processing time saved | 42,000 | labour |
| 3-way match — manual matching time saved | 26,000 | labour |
| 3-way match — overbilling/price-variance recovered | 10,000 | cash |
| Inventory — waste & shrinkage reduction | 9,000 | cash |
| Inventory — manual stock-entry labour eliminated | 19,500 | labour |
| **Gross recurring benefit** | **106,500** | |
| Less: ongoing run cost | (13,000) | cost |
| **Net recurring benefit** | **≈ 93,500 / yr** | |
| One-off working-capital release (~10% of tied-up F&B stock) | +15,000 | one-off (cash, not P&L) |

**FTE freed (full tool) ≈ 1.22** — only the three *labour* pools count (cash recovery and waste are €, not time): (42,000 + 26,000 + 19,500) ÷ €45/h ÷ 1,600 h. **No double-counting:** five distinct pools, time pools feed FTE, cash pools do not.

### A.4 ROI calculation — formula: **ROI = (Net Benefit ÷ Total Cost) × 100**

**Committed AP-only case** (the conservative, defensible headline):

| Horizon | Total cost | Gross saving | Net benefit | **ROI** |
|---|---|---|---|---|
| **12 months** (pilot €20k + rollout €8k + run €13k ≈ €41k) | ≈ €41,000 | ≈ €42,000 | ≈ **+€1,000** | **≈ +2% (≈ breakeven)** |
| **36 months** (Y1 €41k + Y2 €13k + Y3 €13k = €67k) | ≈ €67,000 | ≈ €126,000 | ≈ **+€59,000** | **≈ +88%** |

**Expanded full-tool case** (illustrative, once Phase 2/3 land — same cost base, net €93.5k/yr):

| Horizon | Total cost | Net benefit (cum.) | **ROI** |
|---|---|---|---|
| 12 months | ≈ €41,000 | ≈ €93,500 − ramp | strongly positive |
| 36 months | ≈ €67,000 | ≈ €252,500 (3 × €93.5k − €28k upfront) | **≈ 300%+** |

> The committed AP-only figures are deliberately the ones we stand behind for the go/no-go decision; the full-tool case is the expansion upside, not the promise.

### A.5 Assumptions table

| # | Assumption | Value used | Justification / source | Confidence |
|---|---|---|---|---|
| 1 | Manual cost per invoice | €11–14 | HighRadius/Quadient/Nanonets 2025 (vendor → directional) | Medium |
| 2 | Automated cost per invoice | €2–5 | Same sources; ~70–80% reduction | Medium |
| 3 | Handling time manual → auto | 15 → 3 min | Artsyl 2025 (vendor) | Medium |
| 4 | Loaded finance rate | €45/h | Mid-range EU finance-clerk loaded cost (to confirm with client) | Medium |
| 5 | Invoice volume | ~420/month (~5,040/yr) | Assumed full-property volume for an SME 5★ hotel | **Low — must validate** |
| 6 | Touchless rate at maturity | ~78–88% | Modelled from pilot learning curve | **Low — pilot proves** |
| 7 | Addressable supplier spend (3-way) | ~€1.8M | Assumed F&B + G&A spend for one property | Low |
| 8 | Overbilling recovery | ~0.6% of spend | Conservative vs typical AP leakage findings | Low |
| 9 | Productive hours / FTE / yr | 1,600 h | Standard net-of-leave assumption | High |
| 10 | Pilot duration & cost | 10 wks / €20k | Project 5 cost model | Medium |

### A.6 Break-even

- **Payback ≈ 12 months** including the pilot (AP-only); **≈ 5–6 months** on an ongoing basis once rolled out.
- **Sensitivity (volume-driven):** below **~250 invoices/month** the year-1 return turns **negative** — which is precisely why the pilot gate confirms real volume before any scaling. Above **~600/month** the 3-year AP-only ROI exceeds ~150%.

---

## PART B — Risk Assessment Matrix

Scoring: **Likelihood (1–5) × Impact (1–5) = Risk level.** 🔴 ≥ 12 · 🟡 6–11 · 🟢 ≤ 5. Categories: **Reg** = regulatory · **Tech** = technical · **Eth** = ethical · **Ops** = operational.

| # | Cat. | Risk | L | I | Level | Mitigation |
|---|---|---|---|---|---|---|
| R1 | Tech | Auto-coding accuracy below target on the hotel's real invoice mix (scanned PDFs, new vendors, hallucinated values) | 3 | 4 | 🔴 12 | Human-in-the-loop on **every** entry; confidence threshold routes low-confidence to review; backtest on real invoices during the pilot before any scaling |
| R2 | Reg | Data security — invoices carry vendor PII; processing by third-party LLM and other US services | 3 | 4 | 🔴 12 | Data-processing agreement with each vendor; EU-region processing; data minimisation; no full ledger ingested; see `compliance/gdpr_documentation.md` |
| R3 | Ops | Invoice volume too low for the ROI to clear | 2 | 4 | 🟡 8 | Confirm real monthly volume up front; pilot decision gate kills/holds if volume is thin |
| R4 | Ops | Change resistance / finance-team distrust of "AI doing the books" | 3 | 3 | 🟡 9 | "Second set of eyes" framing; no headcount cuts; training; team keeps final say |
| R5 | Eth | **Automation bias / over-reliance** — staff rubber-stamp AI proposals without genuine review, eroding the human-in-the-loop safeguard | 3 | 4 | 🔴 12 | Surface confidence + the source document side-by-side; mandatory review step that cannot be skipped; periodic spot-audits of approved entries; train staff that they remain accountable |
| R6 | Eth | Misrepresentation in AI-drafted supplier dispute e-mails (tone, wrong figures) damaging a supplier relationship | 2 | 3 | 🟡 6 | Human reviews and sends every e-mail; "prepared with AI, reviewed by our team" disclosure (Art. 50); figures pulled from validated match data |
| R7 | Tech | Invoice quality / format drift (illegible scans, layout changes) degrading extraction | 3 | 2 | 🟡 6 | Exception routing + manual fallback; rising e-invoice share reduces this over time |
| R8 | Reg | EU AI Act / GDPR misstep (wrong classification, missing DPIA, undocumented transfer) | 2 | 4 | 🟡 8 | Limited-risk/transparency classification + DPIA + technical file documented (see `compliance/`); EU-region processing; retention policy |
| R9 | Ops | Tooling cost overrun or vendor pricing change; vendor lock-in | 2 | 3 | 🟡 6 | Usage caps; standard formats (EN 16931 / Peppol); portable architecture across tools |

**Top risks (R1, R2, R5) are all 🔴 and all structural — and all already mitigated by design.** The human-in-the-loop neutralises accuracy risk (R1) but *creates* the automation-bias risk (R5), so R5 is the one to watch most: a safeguard people stop using is no safeguard. None of these blocks a *pilot*; they are exactly what the pilot is meant to prove and control.

---

*Companion deliverables: `eu_ai_act_compliance.md`, `gdpr_documentation.md`, `strategic_plan.md`.*
