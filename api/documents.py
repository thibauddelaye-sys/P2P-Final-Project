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
            if doc.get("attachment"):
                ap = os.path.join(FILES_DIR, _fkey("attach::" + doc["key"]))
                if os.path.exists(ap):
                    with open(ap, "rb") as af:
                        RAW["attach::" + doc["key"]] = (doc["attachment"].get("ctype", "application/octet-stream"), af.read())
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
# --- GL-learned imputation (real accounts + analytics) -------------------
_DATA = os.getenv("DATA_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def _load_lookups():
    for fn in ("gl_lookups.local.json", "gl_lookups.json"):
        p = os.path.join(_DATA, fn)
        if os.path.exists(p):
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            d.setdefault("accounts", {}); d.setdefault("supplier_pos", {})
            d.setdefault("vat_account", {"account": "42161100", "label": "TVA en amont"})
            d.setdefault("payable_account", {"account": "44111000", "label": "Fournisseurs"})
            d.setdefault("journal", "ACH"); d.setdefault("fallback_account", "60380000")
            return d
    return {"accounts": {}, "supplier_pos": {},
            "vat_account": {"account": "42161100", "label": "TVA en amont"},
            "payable_account": {"account": "44111000", "label": "Fournisseurs"},
            "journal": "ACH", "fallback_account": "60380000"}

def _load_keywords():
    p = os.path.join(_DATA, "account_keywords.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}

LOOKUPS = _load_lookups()
KEYWORDS = _load_keywords()

def _acc_label(acc):
    a = LOOKUPS["accounts"].get(acc)
    return a["label"] if a and a.get("label") else acc

def analytics_for(account, supplier=None):
    a = LOOKUPS["accounts"].get(account, {})
    pos = a.get("pos") or "\u2014"; services = a.get("services") or "\u2014"
    pc = a.get("pos_conf", 0); sc = a.get("services_conf", 0)
    inv = a.get("inv_expl") or "EXPLOIT"
    sp = LOOKUPS.get("supplier_pos", {}).get(supplier or "")
    src = "compte"
    if sp:
        pos = sp.get("pos", pos); pc = sp.get("pos_conf", pc); src = "fournisseur"
    return {"services": services, "pos": pos, "inv_expl": inv,
            "services_conf": sc, "pos_conf": pc, "pos_src": src}

def gl_account(desc):
    d = (desc or "").lower()
    for acc, kws in KEYWORDS.items():
        for kw in kws:
            if kw and kw in d:
                return acc, "mot-cl\u00e9"
    return LOOKUPS.get("fallback_account", "60380000"), "d\u00e9faut"

def accounting_entry(doc):
    supplier = doc.get("supplier_name") or ""
    rows, net = {}, 0.0
    for li in (doc.get("line_items") or []):
        u = li.get("unit_price")
        if u is None: continue
        amt = round((li.get("quantity") or 0) * u, 2); net += amt
        acc, basis = gl_account(li.get("description"))
        an = analytics_for(acc, supplier)
        k = (acc, an["pos"], an["services"])
        r = rows.get(k)
        if not r:
            r = rows[k] = {"account": acc, "label": _acc_label(acc), "htva": 0.0,
                           "inv_expl": an["inv_expl"], "pos": an["pos"], "services": an["services"],
                           "pos_conf": an["pos_conf"], "services_conf": an["services_conf"],
                           "pos_src": an["pos_src"], "basis": basis, "edited": False}
        r["htva"] = round(r["htva"] + amt, 2)
    net = round(net, 2)
    ttc = doc.get("total_incl_vat")
    if ttc and ttc > net + 0.01:
        vat = round(ttc - net, 2); assumed = False
    else:
        vat = round(net * 0.17, 2); ttc = round(net + vat, 2); assumed = True
    rate = (vat / net) if net else 0.0
    exp = list(rows.values())
    ov = doc.get("acct_overrides")
    if isinstance(ov, list) and len(ov) == len(exp):
        for r, o in zip(exp, ov):
            if not isinstance(o, dict): continue
            if o.get("account"): r["account"] = o["account"]; r["label"] = _acc_label(o["account"])
            if o.get("pos"): r["pos"] = o["pos"]
            if o.get("services"): r["services"] = o["services"]
            if o.get("inv_expl"): r["inv_expl"] = o["inv_expl"]
            r["edited"] = True; r["basis"] = "manuel"
    for r in exp: r["tva"] = round(r["htva"] * rate, 2)
    diff = round(vat - sum(r["tva"] for r in exp), 2)
    if exp and abs(diff) >= 0.01:
        big = max(exp, key=lambda r: r["htva"]); big["tva"] = round(big["tva"] + diff, 2)
    va = LOOKUPS["vat_account"]; pa = LOOKUPS["payable_account"]
    payable_label = pa.get("label", "Fournisseurs") + " \u2014 " + (supplier or "supplier")
    lines = []
    for r in exp:
        lines.append({"account": r["account"], "label": r["label"], "debit": r["htva"], "credit": None,
                      "htva": r["htva"], "tva": r["tva"], "inv_expl": r["inv_expl"],
                      "pos": r["pos"], "services": r["services"],
                      "pos_conf": r["pos_conf"], "services_conf": r["services_conf"],
                      "pos_src": r["pos_src"], "basis": r["basis"], "edited": r["edited"]})
    lines.append({"account": va.get("account"), "label": va.get("label"), "debit": vat, "credit": None,
                  "htva": None, "tva": None, "inv_expl": None, "pos": None, "services": None})
    lines.append({"account": pa.get("account"), "label": payable_label, "debit": None, "credit": ttc,
                  "htva": None, "tva": None, "inv_expl": None, "pos": None, "services": None})
    debits = [{"account": r["account"], "label": r["label"], "amount": r["htva"]} for r in exp]
    debits.append({"account": va.get("account"), "label": va.get("label"), "amount": vat})
    credit = {"account": pa.get("account"), "label": payable_label, "amount": ttc}
    total_debit = round(sum(d["amount"] for d in debits), 2)
    return {"lines": lines, "journal": LOOKUPS.get("journal", "ACH"),
            "debits": debits, "credit": credit, "net": net, "vat": vat,
            "vat_rate": round(rate, 4), "gross": ttc, "assumed_vat": assumed,
            "balanced": abs(total_debit - ttc) < 0.01}

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
    return {"invoices": out, "count": len(out), "options": _acct_options()}

def mark_posted(key, posted=True):
    d = STORE.get(key)
    if not d: return False
    d["posted"] = posted
    d["posted_at"] = dt.datetime.utcnow().isoformat(timespec="seconds") if posted else None
    _save_state(); return True

def _acct_options():
    accs = sorted(({"account": a, "label": v.get("label", a), "pos": v.get("pos"),
                    "services": v.get("services"), "inv": v.get("inv_expl", "EXPLOIT")}
                   for a, v in LOOKUPS["accounts"].items()), key=lambda x: x["account"])
    pos = LOOKUPS.get("pos_options") or sorted({v.get("pos") for v in LOOKUPS["accounts"].values() if v.get("pos")})
    srv = LOOKUPS.get("services_options") or sorted({v.get("services") for v in LOOKUPS["accounts"].values() if v.get("services")})
    inv = LOOKUPS.get("inv_options") or ["EXPLOIT", "INVEST", "ADM"]
    return {"accounts": list(accs), "pos": list(pos), "services": list(srv), "inv": list(inv)}

def set_acct_overrides(key, lines):
    d = STORE.get(key)
    if not d: return False
    if lines is None:
        d.pop("acct_overrides", None)
    else:
        d["acct_overrides"] = lines
    _save_state(); return True

def receipts():
    out = []
    for d in STORE.values():
        if d.get("doc_type") != "delivery_note": continue
        counted = d.get("counted") or {}
        items = d.get("line_items") or []
        lines = []
        for i, li in enumerate(items):
            delivered = li.get("quantity")
            c = counted.get(str(i))
            diff = (c - delivered) if (c is not None and delivered is not None) else None
            st = "pending" if c is None else ("ok" if diff == 0 else ("over" if (diff or 0) > 0 else "short"))
            lines.append({"i": i, "description": li.get("description"), "delivered": delivered,
                          "counted": c, "diff": round(diff, 2) if diff is not None else None, "status": st})
        counted_n = sum(1 for l in lines if l["counted"] is not None)
        has_diff = any(l["status"] in ("over", "short") for l in lines)
        status = "discrepancy" if has_diff else ("matched" if (items and counted_n >= len(items)) else "pending")
        out.append({"key": d["key"], "doc_number": d.get("doc_number"), "supplier_name": d.get("supplier_name"),
                    "doc_date": d.get("doc_date"), "po_reference": d.get("po_reference"),
                    "has_file": d.get("key") in RAW, "received_at": d.get("received_at"),
                    "counted_by": d.get("counted_by"), "note": d.get("note"), "attachment": d.get("attachment"),
                    "archived": bool(d.get("archived")), "supplier_email": _email_of(d.get("from")),
                    "lines": lines, "status": status})
    out.sort(key=lambda r: ({"pending": 0, "discrepancy": 1, "matched": 2}.get(r["status"], 0), r.get("doc_date") or ""))
    return {"deliveries": out, "count": len(out)}

def save_count(key, counts, counted_by=None, note=None):
    d = STORE.get(key)
    if not d or d.get("doc_type") != "delivery_note": return False
    clean = {}
    for k, v in (counts or {}).items():
        try: clean[str(int(k))] = round(float(v), 3)
        except (TypeError, ValueError): pass
    d["counted"] = clean
    d["counted_by"] = (counted_by or "").strip() or None
    if note is not None:
        d["note"] = note.strip() or None
    d["received_at"] = dt.datetime.utcnow().isoformat(timespec="seconds")
    _save_state(); return True

def attach_receipt(key, filename, content, content_type=""):
    d = STORE.get(key)
    if not d or d.get("doc_type") != "delivery_note": return False
    ct = content_type or _ctype(filename)
    rk = "attach::" + key
    RAW[rk] = (ct, content); _save_raw(rk, ct, content)
    d["attachment"] = {"filename": filename, "ctype": ct}
    _save_state(); return True

def dispute_pdf(key):
    d = STORE.get(key)
    if not d or d.get("doc_type") != "delivery_note": return None
    import fitz
    BX=(0.549,0.110,0.169); CR=(0.984,0.973,0.949); GD=(0.659,0.533,0.310)
    INK=(0.173,0.145,0.125); MUT=(0.46,0.43,0.40); RED=(0.72,0.13,0.13); LN=(0.85,0.83,0.80)
    dl = next((x for x in receipts()["deliveries"] if x["key"] == key), None) or {"lines": []}
    disc = [l for l in dl["lines"] if l["status"] in ("short", "over")]
    doc = fitz.open(); pg = doc.new_page(width=595, height=842)
    def txt(x, y, s, size=10, col=INK, bold=False):
        pg.insert_text((x, y), s if s is not None else "", fontsize=size, color=col, fontname=("hebo" if bold else "helv"))
    def rtxt(xr, y, s, size=10, col=INK, bold=False):
        s = "" if s is None else str(s)
        w = fitz.get_text_length(s, fontsize=size, fontname=("hebo" if bold else "helv"))
        pg.insert_text((xr - w, y), s, fontsize=size, color=col, fontname=("hebo" if bold else "helv"))
    def field(x, y, label, val):
        txt(x, y, label, 8, GD, True); txt(x, y + 14, val or "\u2014", 11, INK)
    pg.draw_rect(fitz.Rect(0, 0, 595, 92), fill=BX, color=BX)
    txt(50, 48, "MAISON LUMI\u00c8RE", 18, CR, True)
    txt(50, 70, "Constat d'\u00e9cart de livraison  \u00b7  Goods-receipt dispute", 10, CR)
    y0 = 125
    field(50, y0, "FOURNISSEUR / SUPPLIER", d.get("supplier_name"))
    field(320, y0, "BON DE LIVRAISON / DELIVERY NOTE", d.get("doc_number"))
    field(50, y0 + 40, "COMMANDE / ORDER", d.get("po_reference"))
    field(320, y0 + 40, "DATE BL", d.get("doc_date"))
    field(50, y0 + 80, "COMPT\u00c9 PAR / COUNTED BY", d.get("counted_by"))
    field(320, y0 + 80, "DATE DU COMPTAGE", (d.get("received_at") or "").replace("T", " ")[:16])
    ty = y0 + 135
    pg.draw_rect(fitz.Rect(50, ty - 14, 545, ty + 4), fill=GD, color=GD)
    txt(56, ty, "ARTICLE", 9, CR, True); rtxt(380, ty, "LIVR\u00c9", 9, CR, True)
    rtxt(450, ty, "COMPT\u00c9", 9, CR, True); rtxt(539, ty, "\u00c9CART", 9, CR, True)
    ty += 22
    if not disc:
        txt(56, ty, "Aucun \u00e9cart enregistr\u00e9 sur cette livraison.", 10, MUT); ty += 20
    for l in disc:
        txt(56, ty, (l["description"] or "")[:48], 10, INK)
        rtxt(380, ty, l["delivered"] if l["delivered"] is not None else "\u2014", 10, INK)
        rtxt(450, ty, l["counted"] if l["counted"] is not None else "\u2014", 10, INK)
        diff = l["diff"]; rtxt(539, ty, ("+" if (diff or 0) > 0 else "") + str(diff), 10, RED, True)
        pg.draw_line(fitz.Point(50, ty + 6), fitz.Point(545, ty + 6), color=LN, width=0.5)
        ty += 24
    ty += 16
    txt(50, ty, "EXPLICATION / EXPLANATION", 8, GD, True); ty += 6
    box = fitz.Rect(50, ty, 545, ty + 72)
    pg.draw_rect(box, color=LN, width=0.7)
    pg.insert_textbox(fitz.Rect(58, ty + 4, 539, ty + 68), d.get("note") or "\u2014", fontsize=10, color=INK, fontname="helv")
    ty += 88
    att = d.get("attachment")
    if att and ("attach::" + key) in RAW and att.get("ctype", "").startswith("image/"):
        txt(50, ty, "PHOTO", 8, GD, True); ty += 8
        try:
            pg.insert_image(fitz.Rect(50, ty, 545, min(ty + 360, 812)), stream=RAW["attach::" + key][1], keep_proportion=True)
        except Exception:
            txt(50, ty + 12, "(photo could not be embedded)", 9, MUT)
    txt(50, 828, "Maison Lumi\u00e8re \u00b7 g\u00e9n\u00e9r\u00e9 le " + dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M") + " \u00b7 document de travail", 8, MUT)
    return doc.tobytes()

def _email_of(s):
    s = (s or "").strip()
    if "<" in s and ">" in s:
        s = s[s.find("<") + 1:s.find(">")].strip()
    return s if ("@" in s and " " not in s) else None

def archive_delivery(key, archived=True):
    d = STORE.get(key)
    if not d or d.get("doc_type") != "delivery_note": return False
    d["archived"] = bool(archived)
    _save_state(); return True

# Re-hydrate persisted documents at startup (kept across restarts when STORE_DIR is a volume).
load()
