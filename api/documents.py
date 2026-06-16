"""Document capture & autonomous matching.
Any emailed document (purchase order / delivery note / invoice) is classified and extracted
by the LLM, stored, and grouped with the others that share the same purchase-order number.
A complete group (PO + delivery note + invoice) is run through a 3-way match.

State is in-memory (fine for a single-worker demo). Sample data lets the page work without
email or an API key.
"""
from __future__ import annotations
import base64, hashlib, json, os, re, datetime as dt

STORE: dict[str, dict] = {}   # key -> document record

RAW: dict[str, tuple] = {}    # key -> (content_type, raw_bytes) -- kept for document preview

EXPENSE_RULES = [
    (re.compile(r"wine|champagne|cr[\u00e9e]mant|riesling|pinot|vin|cognac|gin|vodka|whisky|rum|spirit|beer|bi[\u00e8e]re|lager", re.I), "Beverages"),
    (re.compile(r"water|tonic|cola|juice|jus|orange|soft|coffee|caf[\u00e9e]|espresso", re.I), "Beverages"),
    (re.compile(r"butter|beurre|salmon|saumon|food|foie|gras|cheese|fromage|nourriture|viande|meat|poisson|fish|l[\u00e9e]gume|fruit|pain|bread", re.I), "Food"),
    (re.compile(r"clean|d[\u00e9e]graissant|entretien|detergent|hygi[\u00e8e]n|savon|nettoy", re.I), "Cleaning & consumables"),
]
def expense_category(line_items):
    cats = []
    for li in (line_items or []):
        d = li.get("description") or ""
        hit = "Other"
        for rx, cat in EXPENSE_RULES:
            if rx.search(d):
                hit = cat; break
        if hit not in cats:
            cats.append(hit)
    return " \u00b7 ".join(cats[:3]) if cats else None

def _ctype(filename, fallback=""):
    fn = (filename or "").lower()
    if fn.endswith(".pdf"): return "application/pdf"
    if fn.endswith(".png"): return "image/png"
    if fn.endswith((".jpg", ".jpeg")): return "image/jpeg"
    return fallback or "application/octet-stream"

# ---- persistence (survives restart/redeploy when STORE_DIR points at a Railway volume) ----
STORE_DIR   = os.getenv("STORE_DIR", "runtime_data")
STATE_PATH = os.path.join(STORE_DIR, "store.json")
FILES_DIR  = os.path.join(STORE_DIR, "files")

def _fkey(key): return hashlib.sha1((key or "").encode("utf-8")).hexdigest()

def _save_state():
    try:
        os.makedirs(STORE_DIR, exist_ok=True)
        keep = [d for d in STORE.values() if not str(d.get("key","")).startswith("sample/")]
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(keep, f, ensure_ascii=False)
    except Exception as e:
        print("[persist] save failed:", e)

def _save_raw(key, content_type, content):
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        with open(os.path.join(FILES_DIR, _fkey(key)), "wb") as f:
            f.write(content)
    except Exception as e:
        print("[persist] raw save failed:", e)

def load():
    """Re-hydrate STORE (and raw files) from disk at startup."""
    try:
        if not os.path.exists(STATE_PATH):
            return 0
        with open(STATE_PATH, encoding="utf-8") as f:
            recs = json.load(f)
        for doc in recs:
            STORE[doc["key"]] = doc
            fp = os.path.join(FILES_DIR, _fkey(doc["key"]))
            if os.path.exists(fp):
                with open(fp, "rb") as rf:
                    RAW[doc["key"]] = (doc.get("raw_ctype", "application/octet-stream"), rf.read())
        return len(recs)
    except Exception as e:
        print("[persist] load failed:", e); return 0

def clear():
    """Empty the store and delete its persisted files."""
    STORE.clear(); RAW.clear()
    try:
        if os.path.exists(STATE_PATH): os.remove(STATE_PATH)
        if os.path.isdir(FILES_DIR):
            for fn in os.listdir(FILES_DIR):
                try: os.remove(os.path.join(FILES_DIR, fn))
                except Exception: pass
    except Exception as e:
        print("[persist] clear failed:", e)

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

def ingest(items: list[dict], source: str = "email") -> int:
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
                    "subject":it.get("subject"), "source":source,
                    "expense_type":expense_category(doc.get("line_items")),
                    "captured_at":dt.datetime.utcnow().isoformat(timespec="seconds")})
        ct = _ctype(it["filename"]); doc["raw_ctype"] = ct
        STORE[key] = doc; RAW[key] = (ct, it["content"]); _save_raw(key, ct, it["content"]); added += 1
    if added: _save_state()
    return added

def ingest_upload(filename: str, content: bytes, content_type: str = "") -> dict:
    """Drag-and-drop / manual upload of a single document."""
    key = f"manual/{filename}/{hashlib.sha1(content).hexdigest()[:8]}"
    if key in STORE:
        return STORE[key]
    try:
        doc = extract_document(content, filename, content_type)
    except Exception as e:
        doc = {"doc_type":"unknown","error":str(e),"line_items":[]}
    doc.update({"key":key, "filename":filename, "from":"manual upload", "subject":None,
                "source":"manual", "expense_type":expense_category(doc.get("line_items")),
                "captured_at":dt.datetime.utcnow().isoformat(timespec="seconds")})
    ct = content_type or _ctype(filename); doc["raw_ctype"] = ct
    STORE[key] = doc; RAW[key] = (ct, content); _save_raw(key, ct, content); _save_state()
    return doc

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
        d["has_file"] = d.get("key") in RAW
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
                  "from":"sample","subject":"(sample)","source":"email",
                  "expense_type":expense_category(d.get("line_items")),
                  "captured_at":dt.datetime.utcnow().isoformat(timespec="seconds")})
        STORE[d["key"]] = d
    return len(sample)

# ---- accounting: propose a double-entry journal for each invoice ----
GL_RULES = [
    (re.compile(r"wine|champagne|cr[\u00e9e]mant|riesling|pinot", re.I), ("6022", "Beverages \u2014 wine")),
    (re.compile(r"spirit|cognac|whisky|malt|gin|vodka|rum", re.I),        ("6022", "Beverages \u2014 spirits")),
    (re.compile(r"beer|lager|ipa|pils|bi[\u00e8e]re", re.I),             ("6022", "Beverages \u2014 beer")),
    (re.compile(r"water|tonic|cola|juice|jus|orange|soft", re.I),         ("6023", "Beverages \u2014 soft")),
    (re.compile(r"coffee|caf[\u00e9e]|espresso|bean", re.I),             ("6024", "F&B \u2014 coffee")),
    (re.compile(r"food|butter|beurre|salmon|saumon|foie|gras|cheese|fromage|meat|viande|fish|poisson|bread|pain", re.I), ("6021", "Food purchases")),
    (re.compile(r"clean|d[\u00e9e]graissant|entretien|detergent|hygi[\u00e8e]n|savon|nettoy", re.I), ("6063", "Cleaning & consumables")),
]
def gl_account(desc):
    x = desc or ""
    for rx, acc in GL_RULES:
        if rx.search(x): return acc
    return ("6028", "Other F&B")

def accounting_entry(doc):
    by_acc, net = {}, 0.0
    for li in (doc.get("line_items") or []):
        u = li.get("unit_price")
        if u is None: continue
        amt = round((li.get("quantity") or 0) * u, 2); net += amt
        acc = gl_account(li.get("description"))
        by_acc[acc] = round(by_acc.get(acc, 0.0) + amt, 2)
    net = round(net, 2)
    ttc = doc.get("total_incl_vat")
    if ttc and ttc > net + 0.01:
        vat = round(ttc - net, 2); assumed = False
    else:
        vat = round(net * 0.17, 2); ttc = round(net + vat, 2); assumed = True
    debits = [{"account": c, "label": l, "amount": a} for (c, l), a in sorted(by_acc.items())]
    debits.append({"account": "44566", "label": "Input VAT", "amount": vat})
    credit = {"account": "4011", "label": "Accounts payable \u2014 " + (doc.get("supplier_name") or "supplier"), "amount": ttc}
    total_debit = round(sum(d["amount"] for d in debits), 2)
    return {"debits": debits, "credit": credit, "net": net, "vat": vat,
            "vat_rate": round(vat/net, 4) if net else 0.0, "gross": ttc,
            "assumed_vat": assumed, "balanced": abs(total_debit - ttc) < 0.01}

def accounting():
    out = []
    for d in STORE.values():
        if d.get("doc_type") != "invoice": continue
        out.append({"key": d["key"], "doc_number": d.get("doc_number"), "supplier_name": d.get("supplier_name"),
                    "doc_date": d.get("doc_date"), "currency": d.get("currency") or "EUR",
                    "po_reference": d.get("po_reference"), "has_file": d.get("key") in RAW,
                    "posted": bool(d.get("posted")), "posted_at": d.get("posted_at"),
                    "entry": accounting_entry(d)})
    out.sort(key=lambda r: (r["posted"], r.get("doc_date") or "", r.get("doc_number") or ""))
    return {"invoices": out, "count": len(out)}

def mark_posted(key, posted=True):
    d = STORE.get(key)
    if not d: return False
    d["posted"] = posted
    d["posted_at"] = dt.datetime.utcnow().isoformat(timespec="seconds") if posted else None
    _save_state(); return True

# Re-hydrate persisted documents at startup (kept across restarts when STORE_DIR is a volume).
load()
