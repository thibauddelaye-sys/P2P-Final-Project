# GDPR Documentation — Maison Lumière "P2P"
*Ironhack Final Project · `compliance/gdpr_documentation.md`*

> **Scope note.** The public/demo build runs on **synthetic data** (fictional suppliers, pseudonymised/generic GL, a test mailbox) — so no real personal data is processed *today*. This package assesses the system **as if deployed in production** at the hotel, processing **real** supplier and staff data, because that is where the obligations apply. **Not a legal opinion** — engage the client's DPO/legal counsel before relying on this for compliance decisions.

---

## 1. Does the system process personal data? — Yes (in production)

In production the system processes personal data, primarily **business-contact and operational** data (not special-category data):
- **Supplier contact data** — names and e-mail addresses of supplier-side individuals on invoices/POs/delivery notes and in the mailbox.
- **Staff identifiers** — the name/identifier of the hotel employee who captured a document or counted a delivery (audit trail).
- **Incidental personal data inside documents** — e.g. a named individual on a sole-trader invoice, a delivery contact.

**Special-category data (Art. 9): none.** Invoices and inventory documents do not carry health, biometric, political, religious, sexual-orientation, ethnic-origin or trade-union data, and none is inferable from the outputs (which are accounting entries and discrepancy flags, not inferences about individuals). **Cross-border:** yes — data leaves the EEA (see §5).

---

## 2. Data flow map

```
                       ┌─────────────────────────── MAISON LUMIÈRE (controller) ───────────────────────────┐
 Supplier e-mails ──►  │  Gmail mailbox  ──►  P2P app (FastAPI on Railway, /store volume)  ──►  CSV journal │
 Manual uploads ─────► │        │                     │            │              │                          │
 (PDF/JPG/PNG)         │        │                     │            │              └──► GL/accounting export   │
                       └────────┼─────────────────────┼────────────┼──────────────────────────────────────-─┘
                                ▼                     ▼            ▼
                          Google (Gmail)        Anthropic       Resend
                          mailbox storage     (Claude API)    (dispute e-mail
                              [US infra]     doc → extraction   + PDF + photo)
                                              [US]               [US]
                                                 │
                                                 ▼
                                            LangSmith
                                         (trace metadata +
                                          extracted output)
                                          [EU or US endpoint]
```

**Personal data per hop (production):** supplier docs (PII) → mailbox (Google) and → app store (Railway); each doc → Anthropic for extraction; extracted fields → LangSmith trace; dispute e-mail (recipient + content + attachments) → Resend. Storage of record is the Railway volume.

---

## 3. Processing activities register

| Data category | Purpose of processing | Legal basis (Art. 6) | Retention | Third-party recipients |
|---|---|---|---|---|
| Supplier invoice/PO/DN content (incl. contact PII) | Read & extract; 3-way match; propose & post accounting entry | **(b) Contract** (perform supplier contract) + **(c) Legal obligation** (accounting/tax record-keeping) + **(f) Legitimate interests** (accurate, efficient AP; overbilling prevention) | The **accounting record**: ~10 yrs (LU commercial/tax law). The **raw image + trace + intermediate data**: minimise — purge after a short operational window (e.g. 30–90 days) | Anthropic (extraction), Railway (storage), LangSmith (trace) |
| Supplier contact data (name, e-mail) | Supplier communication; dispute handling | **(b) Contract** + **(f) Legitimate interests** | Duration of the supplier relationship + legal retention of correspondence | Resend (e-mail send), Google (mailbox), Railway |
| Staff identifier (captured-by / counted-by) | Internal audit trail / accountability | **(f) Legitimate interests** (in the employment context — must be proportionate and transparent to staff) | Life of the accounting record; minimise where possible | Railway (storage) |
| Incoming e-mail metadata (sender address) | Ingest invoices that arrive by e-mail | **(b) Contract** + **(f) Legitimate interests** | Mailbox retention policy (e.g. purge processed mail) | Google (Gmail) |

> **Legitimate-interests note (Art. 6(1)(f)):** the interest is legitimate (efficient, accurate AP and overbilling prevention); the processing is necessary (payables cannot be handled without the invoice data); and the balancing test favours processing because the data is low-sensitivity business-context data that suppliers reasonably expect to be processed for billing. A short LIA should be **documented** for the staff-attribution and legitimate-interests uses (accountability, Art. 5(2)).

---

## 4. DPIA — highest-risk processing activity

**Processing assessed:** *Sending supplier-document content to a third-party general-purpose AI model (Anthropic, US) for extraction, with tracing to LangSmith* — the highest-risk activity because it combines **personal data + innovative technology + international transfer**.

**4.1 Description.** Each captured supplier document (which in production contains supplier contact PII and possibly other individuals) is base64-encoded and sent to Anthropic's Claude API for structured extraction. The extracted output (supplier name, numbers, amounts) is traced to LangSmith. The document and output leave the EEA.

**4.2 Necessity & proportionality.** The automated extraction is the core value and is **necessary** to remove manual keying; no less-intrusive method achieves the same (template OCR fails on heterogeneous formats). Proportionality is supported by: human-in-the-loop on every entry, no full ledger ingested, and the ability to use zero-retention/region options at the model provider. Raw-byte redaction is already applied to the top-level trace.

**4.3 Risks to data subjects.**
- Supplier/staff personal data processed outside the EEA without (yet) a documented transfer mechanism.
- The extracted **output** (and, via the wrapped client, potentially the **full document payload**) may reach LangSmith despite raw-byte redaction of the top-level trace.
- Indefinite retention on the storage volume (no automatic purge) → data kept longer than necessary.
- No information provided to the data subjects (suppliers/staff) about this processing.

**4.4 Mitigation measures.**
- **DPAs** with Anthropic, Resend, Railway, Google and LangSmith (Art. 28) before any real data flows.
- **Keep processing in-region:** set LangSmith to its **EU endpoint** (`eu.api.smith.langchain.com`); use the model provider's EU/zero-retention options; prefer EU hosting region where available.
- **Redact the trace output**, not only inputs; or disable tracing in production.
- **Retention/purge policy:** short TTL on raw uploads and traces; long retention only for the legal accounting record.
- **Transparency:** publish a privacy notice to suppliers/staff (Art. 13/14).
- Human-in-the-loop (already in place) prevents any automated decision with legal effect.

**4.5 Residual risk rating.** With the mitigations in place: **Low–Medium.** Without them (current production-readiness state): **Medium–High**, driven by the missing DPAs, undocumented transfers and indefinite retention. None of these affects the synthetic demo today; all must be closed before real-data deployment.

---

## 5. Third-party data transfers

| Service | Data sent | Legal mechanism (to put in place) | Where processed/stored |
|---|---|---|---|
| **Anthropic (Claude API)** | Full document content (incl. PII) for extraction | DPA + EU SCCs (or EU-US DPF if certified); enable zero-retention | US (configurable region/retention) |
| **Railway** (hosting) | All persisted documents, extracted data, attachments | DPA + EU SCCs | US (West) — prefer an EU region if available |
| **Resend** (e-mail) | Dispute e-mail recipient, body, PDF + photo attachments | DPA + EU SCCs (or DPF if certified) | US |
| **Google / Gmail** (mailbox) | Incoming supplier e-mails + attachments + sender addresses | Google Workspace DPA (Google is DPF-certified) | Google infrastructure |
| **LangSmith** (tracing) | Trace metadata (filename, content-type) + extracted output (+ possibly document payload via the wrapped client) | DPA + EU SCCs **or** set the **EU endpoint** to keep traces in-region | EU **or** US depending on endpoint |

**Current state:** **no DPAs are in place and no transfer mechanism is documented** — acceptable for a synthetic demo, but a **blocking gap** before processing real personal data. Quick win: switch LangSmith to the EU endpoint.

### 5a. Model choice & EU data residency (production)

The largest transfer is the **document content sent to the LLM**. Three ways to address it, ordered by how cleanly they remove the transfer:

1. **Keep Claude, but process in the EU.** The direct Anthropic API has no EU-only region (US/global only), but Claude can be run inside the EU via **AWS Bedrock EU regions** (Frankfurt, Ireland, Paris, Stockholm) or **Google Vertex AI EU regions**, combined with Anthropic's DPA (EU SCCs included) and **Zero-Data-Retention**. Keeps the already-validated model; processing stays in the EEA. *Residual:* Anthropic is US-incorporated, so US CLOUD Act exposure persists even with EU hosting.
2. **Switch to an EU-native model — e.g. Mistral (Paris).** EU data residency **by default** (US routing is opt-in), not subject to the US CLOUD Act, DPA available for business customers, and capable of the extraction task (Pixtral handles document understanding/OCR; an invoice-processing agent builder exists). This is the **strongest residency + data-sovereignty posture** and a strong narrative for an EU hotel. *Trade-off:* extraction accuracy on this hotel's real invoice mix must be **validated** (the pilot backtest is the place to do it).
3. **Self-host an open-weight model** (Mistral/Llama) on EU or on-premises infrastructure — no third-party model provider at all; maximum assurance, highest operational cost.

> Switching to **another US provider** (OpenAI, Google direct) gives **no GDPR benefit** — the same international transfer and CLOUD Act exposure apply. The extraction is isolated in a single function (`extract_document`), so the model is **swappable** without touching the rest of the system.

**Recommendation:** for the demo/MVP, Claude is fine (it works and is isolated). For production at an EU hotel, prefer **Claude via Bedrock/Vertex EU + DPA + ZDR** *or* an **EU-native model (Mistral)**; the latter removes the transfer entirely and fits the sovereignty story best.

---

## 6. Data subject rights — how the system supports them

| Right | Current support | Gap / action for production |
|---|---|---|
| **Access (Art. 15)** | A data subject's documents are retrievable from the store | No formal DSAR workflow; data also lives in the mailbox, Resend logs and traces — need an orchestrated lookup across all processors |
| **Erasure (Art. 17)** | Per-document delete (and full clear) implemented | Not orchestrated across processors — erasure must also cover the mailbox, sent-e-mail logs and LangSmith traces (and confirm Anthropic zero-retention) |
| **Rectification (Art. 16)** | The accounting page is line-by-line **editable**, so extracted data can be corrected before/after posting | Adequate for the core record; log corrections for accountability |
| **Portability (Art. 20)** | Data exports as CSV (GL journal, stock-in) | Partial; portability mainly relevant to data provided by a data subject — limited applicability here |
| **Objection (Art. 21)** | — | Legitimate-interests processing → right to object applies; provide a contact route and a manual handling path (relevant mainly to the staff-attribution use) |

---

## 7. Law-stacking & accountability check

- **AI Act:** classified **limited-risk/transparency** (see `eu_ai_act_compliance.md`). It adds **no obligation GDPR doesn't already cover**, except the Art. 50 transparency line — which also reinforces GDPR Art. 13/14 transparency.
- **ePrivacy:** the cockpit is an internal tool with **no marketing cookies/trackers** (verified — only `/health` and `/api` calls). ePrivacy consent **not triggered**; confirm no analytics are added later.
- **Data Act:** **N/A** — no connected-product/IoT data or cloud-switching scope.
- **Accountability (Art. 5(2)) — could we show compliance to a regulator with what exists today?** **Not yet.** Missing: DPAs, a transfer-mechanism record, a documented LIA, a retention schedule, a privacy notice, and this register/DPIA in maintained form. The data-protection-by-design posture is strong (synthetic demo, secrets and real GL git-ignored, human-in-the-loop, raw-byte trace redaction), but the **documentation set** must be completed before production.

---

## 8. Bottom line (for the client's DPO)

**Proceed with conditions.** The system is well-architected from a privacy standpoint and processes only low-sensitivity business data with a human on every decision — but before any real personal data flows, the controller must, in order: **(1)** put DPAs in place with all five processors; **(2)** document the international-transfer mechanism and switch LangSmith to the EU endpoint; **(3)** implement a retention/purge policy and a cross-processor erasure path; **(4)** publish a supplier/staff privacy notice. Residual risks even then: reliance on US sub-processors' ongoing adequacy, and extraction accuracy on edge-case documents (mitigated by human review).
