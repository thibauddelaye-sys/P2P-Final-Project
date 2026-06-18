# EU AI Act Compliance — Maison Lumière "P2P"
*Ironhack Final Project · `compliance/eu_ai_act_compliance.md`*

> First-pass compliance package for an AI-assisted accounts-payable & inventory tool. **Not a legal opinion** — role mapping and the Article 50 question should be confirmed with counsel before any market representation or filing.

---

## 1. Risk classification

**Classification: LIMITED RISK (transparency obligations under Article 50).**

The operational core of the system — reading invoices, proposing entries, matching orders — is, on its own, **minimal-risk**: it automates an internal back-office task and makes no decisions about people. However, the system also uses **generative AI to produce outward-facing text** (the supplier dispute e-mails it drafts) and internal narratives. That generative component brings the system within the scope of **Article 50 transparency duties**, so the system as a whole is classified — conservatively and defensibly — as **limited risk / transparency**, and the corresponding obligations are met.

> *Reconciliation note.* An earlier quick read called this "minimal risk", focusing on the operational core and the strong argument that the AI-drafted e-mails fall under Article 50's assistive-function exception. For a formal classification we take the more conservative position: a system that generates content sent to third parties is best placed in the transparency tier, and we then **document and meet** the transparency obligations rather than rely on the exception. This is the safer call for a graded/auditable assessment and is consistent with the Project 5 framing.

---

## 2. Classification reasoning — step by step

**Step 1 — Is it prohibited (Article 5)? → NO.** No social scoring, no subliminal/manipulative techniques, no exploitation of vulnerabilities, no biometric categorisation, no untargeted facial scraping, no emotion recognition, no real-time remote biometric identification. None of the eight prohibitions is engaged.

**Step 2 — Is it high-risk (Annex III)? → NO.** Walking the eight high-risk areas:

| Annex III area | Applies? | Why |
|---|---|---|
| 1. Biometrics | No | No biometric data processed |
| 2. Critical infrastructure | No | Internal AP tool, not infrastructure safety management |
| 3. Education / vocational training | No | — |
| 4. **Employment / worker management** | **No** | Records *who captured/counted* as an **audit trail**, but does **not** recruit, evaluate, rank, allocate tasks to, or monitor the performance of workers |
| 5. **Essential services / creditworthiness** | **No** | Processes the hotel's *own payables*; does **not** assess the creditworthiness of, or gate any service to, natural persons |
| 6. Law enforcement | No | — |
| 7. Migration / asylum / border | No | — |
| 8. Administration of justice / democracy | No | — |

The two areas worth checking (4 and 5) are explicitly **not** triggered because the system makes decisions *about invoices and stock, not about people*, always under human review.

**Step 3 — Does it trigger transparency duties (Article 50)? → YES.** The system **generates text content** (dispute e-mails, narratives) with AI. Article 50(2) brings AI-generated content within transparency scope. We therefore classify at **limited risk** and apply the disclosure obligations below, rather than relying on the assistive-function exception.

**Step 4 — General-purpose AI (GPAI) layer.** The system is built **on** a general-purpose model (Anthropic Claude) via API, with no fine-tuning. The **model-level GPAI obligations (Art. 53–55)** therefore sit with **Anthropic as the GPAI provider**, not with us (the system provider) or the hotel (the deployer). We do not inherit GPAI-provider status by calling the API.

---

## 3. Mandatory requirements summary (Limited risk → Article 50 transparency)

| Obligation | What Article 50 requires | How our design addresses it |
|---|---|---|
| **Disclosure of AI-generated content** | Recipients/affected persons should be able to know content is AI-generated/assisted | Add a standing line to AI-drafted supplier e-mails: *"prepared with AI assistance and reviewed by a member of the Maison Lumière finance team."* Internal "AI reads, humans decide" framing is visible in the cockpit. |
| **Disclosure to staff (interacting with the AI)** | Users should know they are working with an AI system | A short internal notice describes what the AI does, its known failure modes, and the rule that humans verify every entry. |
| **Clear, accessible disclosure** | Information given in a clear and distinguishable manner, at the latest at first interaction | The e-mail footer and the staff notice are plain-language and always present. |

Because the system is **not** high-risk, the heavy provider obligations (risk-management system, data governance file, conformity assessment, CE marking, registration, post-market monitoring under Art. 9–15, 43, 47–49, 72) **do not apply**. The substantive obligations for this system live under **data-protection law** (see `gdpr_documentation.md`).

---

## 4. Conformity Assessment Summary

*A formal-style summary of the system's position. (No third-party conformity assessment is required at this risk level; this is a self-assessment.)*

**4.1 What the system does.** An AI-assisted accounts-payable and inventory tool for an independent 5★ hotel. It captures supplier documents, uses a large language model to extract structured data, proposes the accounting entry, runs a 3-way match (ordered vs received vs billed), supports goods-receipt control, and drafts supplier dispute e-mails. A finance team member reviews and approves every output; nothing is posted, paid or sent autonomously.

**4.2 Risk class and basis.** **Limited risk (Article 50 transparency).** Basis: not prohibited (Art. 5); not in any Annex III high-risk area (it automates internal finance/inventory tasks and makes no decisions about natural persons, under human review); but it generates outward-facing text content, which brings it within Article 50's transparency scope. The underlying general-purpose model's obligations rest with its provider (Anthropic).

**4.3 Applicable obligations and how the design addresses them.**
- *Transparency to recipients of AI-generated content* → disclosure line on AI-drafted supplier e-mails.
- *Transparency to users/staff* → internal AI-use notice.
- *Meaningful human oversight* (carried over as best practice and as the core of the low-risk posture) → mandatory, non-skippable human review of every proposed entry and every e-mail; "AI reads, humans decide" is a hard design boundary.
- *Professional diligence & AI literacy (Art. 4, good practice)* → staff guidance on the model's limits.

**4.4 Gaps not yet addressed, and how they would be resolved before deployment.**

| Gap | Resolution before deployment |
|---|---|
| The AI-assistance disclosure line is specified but not yet added to the live e-mail template | Add the standing footer to the supplier-e-mail builder (≈1h) |
| No internal AI-use notice is published to staff | Publish the half-page notice (drafted in this package) at onboarding |
| Data-protection artefacts (DPAs, transfer mechanism, retention policy, DSAR workflow) are not yet in place | Resolve under the GDPR package — these are the **binding** items for this system; requires the client's DPO/legal counsel |
| Classification is a self-assessment | Confirm the Article 50 position and role map with legal counsel |

**4.5 Caveat.** This is a first-pass self-assessment, not a legal opinion, not a third-party conformity assessment, and not a certification.

---

## 5. Technical Documentation Outline

*Skeleton of the technical file that would accompany the system (modelled on Annex IV; a limited-risk system does not require the full file, but maintaining it is good practice and supports the GDPR/accountability work).*

1. **General description** — purpose, intended users, deployment context, version.
2. **System architecture** — capture → extraction (LLM) → grouping/dedup → imputation → 3-way match → goods receipt → export; data stores; third-party services.
3. **AI component specification** — model used (Claude Haiku), prompt/schema, max-tokens, JSON-repair fallback, swap path to Sonnet; the GPAI provider's model card reference.
4. **Data** — input types and sources; the chart-of-accounts/vendor-master lookups; pseudonymisation approach; what is and is not stored.
5. **Human-oversight design** — the mandatory review step, editable proposals, confidence/threshold routing, "no autonomous posting/sending" boundary.
6. **Accuracy, robustness & monitoring** — extraction quality on the test set, degraded-scan handling, exception routing, LangSmith tracing, accuracy-drift monitoring (planned).
7. **Cybersecurity** — secrets management (env vars, never committed), transport security (HTTPS), access model (planned: auth/RBAC).
8. **Transparency measures** — the Article 50 disclosures (staff notice + e-mail footer).
9. **Data-protection cross-reference** — link to `gdpr_documentation.md` (processing register, DPIA, transfers, DSAR).
10. **Limitations & known risks** — cross-reference to `roi_risk_assessment.md` risk matrix.
11. **Change log & versioning** — material changes, especially any feature that could affect classification (e.g. autonomous sending, staff evaluation → would re-trigger assessment).

---

*Companion deliverable: `gdpr_documentation.md` — where this system's binding obligations actually sit.*
