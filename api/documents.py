"""Document capture & autonomous matching.
Any emailed document (purchase order / delivery note / invoice) is classified and extracted
by the LLM, stored, and grouped with the others that share the same purchase-order number.
A complete group (PO + delivery note + invoice) is run through a 3-way match.

State is in-memory (fine for a single-worker demo). Sample data lets the page work without
email or an API key.
"""
from __future__ import annotations
import base64, json, os, re, datetime as dt

STORE: dict[str, dict] = {}   # key -> document record

DOC_PROMPT = (
    "You are an accounts-payable assistant. Classify this supplier document and extract its data. "
    "Return ONLY JSON, no prose, no markdown. Schema: "
    '{"doc_type": "purchase_order"|"delivery_note"|"invoice"|"unknown", '
    '"doc_number": str, "po_reference": str, "supplier_name": str, "doc_date": str, '
    '"currency": str, "line_items": [{"description": str, "quantity": number, "unit_price": number|null}], '
    '"total_incl_vat": number|null}. '
    "Map French titles: 'BON DE COMMANDE' -> purchase_order, 'BON DE LIVRAISON' -> delivery_note, "
    "'FACTURE' -> invoice. po_reference is the purchase-order number the document relates to "
    "(for a purchase order, its own number; for a delivery note or invoice, the order it cites, "
    "often labelled 'Réf. commande' / 'Commande'). For a delivery note unit_price is usually null. "
    "Use null if a field is absent. Do not invent values."
)

def extract_document(raw: bytes, filename: str, content_type: str = "") -> dict:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    b64 = base64.standard_b64encode(raw).decode()
    ct, fn = (content_type or "").lower(), (filename or "").lower()
    if "pdf" in ct or fn.endswith(".pdf"):
        block = {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":b64}}
    else:
        media = "image/png" if "png" in ct or fn.endswith(".png") else "image/jpeg"
        block = {"type":"image","source":{"type":"base64","media_type":media,"data":b64}}
    from anthropic import Anthropic
    msg = Anthropic().messages.create(
        model=os.getenv("EXTRACT_MODEL","claude-haiku-4-5-20251001"), max_tokens=1600,
        messages=[{"role":"user","content":[block,{"type":"text","text":DOC_PROMPT}]}])
    text = "".join(b.text for b in msg.content if getattr(b,"type","")=="text")
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)

def ingest(items: list[dict]) -> int:
    """items: from email_intake.fetch_invoice_attachments (content, filename, from, subject, msg_id)."""
    added = 0
    for it in items:
        key = f"{it.get('msg_id','')}/{it['filename']}"
        if key in STORE:               # already captured -> skip (no re-extraction)
            continue
        try:
            doc = extract_document(it["content"], it["filename"], "")
        except Exception as e:
            doc = {"doc_type":"unknown","error":str(e),"line_items":[]}
        doc.update({"key":key, "filename":it["filename"], "from":it.get("from"),
                    "subject":it.get("subject"), "captured_at":dt.datetime.utcnow().isoformat(timespec="seconds")})
        STORE[key] = doc; added += 1
    return added

def _norm(s): return re.sub(r"[^A-Z0-9]", "", (s or "").upper())
def _key(desc):
    m = re.findall(r"[A-Za-zÀ-ÿ]+", desc or "")
    return m[0].lower() if m else (desc or "").strip().lower()

def three_way(docs: list[dict]) -> dict:
    po  = next((d for d in docs if d.get("doc_type")=="purchase_order"), None)
    bl  = next((d for d in docs if d.get("doc_type")=="delivery_note"), None)
    inv = next((d for d in docs if d.get("doc_type")=="invoice"), None)
    def idx(d): return {_key(li.get("description")): li for li in (d.get("line_items") or [])} if d else {}
    pol, bll, invl = idx(po), idx(bl), idx(inv)
    lines, overpay, exc = [], 0.0, 0
    for k, iv in invl.items():
        pv, dv = pol.get(k), bll.get(k)
        qb = iv.get("quantity"); qo = pv.get("quantity") if pv else None
        qr = dv.get("quantity") if dv else None
        pp = pv.get("unit_price") if pv else None; ip = iv.get("unit_price")
        flags = []
        if pv is None: flags.append("NOT_ON_PO")
        if dv is None: flags.append("NOT_ON_DELIVERY")
        if qr is not None and qb is not None and qb > qr: flags.append("OVERBILLED_QTY")
        if pp is not None and ip is not None and abs(ip-pp) > 0.01: flags.append("PRICE_VARIANCE")
        op = 0.0
        if "PRICE_VARIANCE" in flags and ip is not None and pp is not None: op += (ip-pp)*(qb or 0)
        if "OVERBILLED_QTY" in flags and ip is not None: op += (qb-qr)*ip
        overpay += op; exc += 1 if flags else 0
        lines.append({"description": iv.get("description"), "qty_ordered": qo, "qty_received": qr,
                      "qty_billed": qb, "po_price": pp, "inv_price": ip,
                      "flags": flags, "overpay_eur": round(op,2)})
    return {"lines": lines, "status": "MATCHED" if exc==0 else "EXCEPTION",
            "exceptions": exc, "overpay_eur": round(overpay,2)}

def grouped() -> dict:
    groups, loose = {}, []
    for d in STORE.values():
        ref = _norm(d.get("po_reference"))
        (groups.setdefault(ref, []).append(d) if ref else loose.append(d))
    out = []
    for ref, docs in sorted(groups.items()):
        types = {d.get("doc_type") for d in docs}
        complete = {"purchase_order","delivery_note","invoice"} <= types
        out.append({"po_reference": ref,
                    "supplier": next((d.get("supplier_name") for d in docs if d.get("supplier_name")), None),
                    "documents": docs, "present": sorted(t for t in types if t),
                    "complete": complete, "match": three_way(docs) if complete else None})
    return {"groups": out, "loose": loose, "count": len(STORE)}

# ---- sample data (mirrors the 6 demo PDFs) so the page works without email/API ----
def load_sample():
    def doc(dt_, num, ref, sup, date, items, total):
        return {"doc_type":dt_, "doc_number":num, "po_reference":ref, "supplier_name":sup,
                "doc_date":date, "currency":"EUR", "line_items":items, "total_incl_vat":total}
    caves=[{"description":"Crémant de Luxembourg Brut 75cl","quantity":48,"unit_price":12.40},
           {"description":"Riesling Grand Cru 2022 75cl","quantity":24,"unit_price":17.90},
           {"description":"Cognac VSOP 70cl","quantity":6,"unit_price":42.00},
           {"description":"Gin London Dry 70cl","quantity":12,"unit_price":19.50}]
    caves_bl=[{**li,"unit_price":None} for li in caves]
    dpo=[{"description":"Beurre doux plaquette 250g","quantity":80,"unit_price":1.60},
         {"description":"Saumon fumé tranché 1kg","quantity":12,"unit_price":22.00},
         {"description":"Jus d'orange pressé 1L","quantity":60,"unit_price":1.80},
         {"description":"Dégraissant cuisine professionnel 5L","quantity":6,"unit_price":14.50}]
    dinv=[dict(li) for li in dpo]; dinv[1]={**dinv[1],"unit_price":24.00}   # Saumon overbilled
    dbl=[{**li,"unit_price":None} for li in dpo]
    sample = [
      doc("purchase_order","PO-2024-0087","PO-2024-0087","Caves du Grand-Duché S.à r.l.","05/03/2024",caves,None),
      doc("delivery_note","BL-2024-0312","PO-2024-0087","Caves du Grand-Duché S.à r.l.","08/03/2024",caves_bl,None),
      doc("invoice","FAC-2024-0312","PO-2024-0087","Caves du Grand-Duché S.à r.l.","12/03/2024",caves,1767.64),
      doc("purchase_order","PO-2024-0091","PO-2024-0091","Distrifood Lux S.à r.l.","02/03/2024",dpo,None),
      doc("delivery_note","BL-24-1145","PO-2024-0091","Distrifood Lux S.à r.l.","06/03/2024",dbl,None),
      doc("invoice","FAC-24-1145","PO-2024-0091","Distrifood Lux S.à r.l.","08/03/2024",dinv,None),
    ]
    for d in sample:
        d.update({"key":f"sample/{d['doc_number']}","filename":f"{d['doc_number']}.pdf",
                  "from":"sample","subject":"(sample)","captured_at":dt.datetime.utcnow().isoformat(timespec="seconds")})
        STORE[d["key"]] = d
    return len(sample)
