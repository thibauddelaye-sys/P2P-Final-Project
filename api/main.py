"""P2P + Inventory API — 3-way match, stock ledger, barcode scan, AI document extraction.
Separate service from the Project 5 repo. Demo: synthetic data, real logic, real AI extraction.

Run:  pip install -r requirements.txt  &&  uvicorn api.main:app --reload --port 8100
"""
from __future__ import annotations
import base64, json, os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

DATA = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
app = FastAPI(title="P2P & Inventory API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def load():
    d = {}
    for name in ["products","purchase_orders","delivery_notes","invoices",
                 "three_way_match","stock_ledger","reorder_status"]:
        d[name] = pd.read_csv(DATA / f"{name}.csv")
    return d
DB = load()
# live stock balances held in memory so scanning actually decrements during the demo
STOCK = {r["sku"]: int(r["balance"]) for _, r in DB["reorder_status"].iterrows()}
PRODUCTS = {r["sku"]: r for _, r in DB["products"].iterrows()}
EAN2SKU = {str(r["ean13"]): r["sku"] for _, r in DB["products"].iterrows()}

def recs(df): return json.loads(df.to_json(orient="records"))

@app.get("/health")
def health(): return {"status": "ok", "invoice_lines": int(len(DB["three_way_match"]))}

# ---- 3-way match ----------------------------------------------------------
@app.get("/api/match")
def match():
    m = DB["three_way_match"]
    return {
        "summary": {
            "lines": int(len(m)),
            "matched": int((m["status"] == "MATCHED").sum()),
            "exceptions": int((m["status"] == "EXCEPTION").sum()),
            "overbilled": int(m["flags"].str.contains("OVERBILLED").sum()),
            "price_variance": int(m["flags"].str.contains("PRICE_VARIANCE").sum()),
            "short_delivery": int(m["flags"].str.contains("SHORT_DELIVERY").sum()),
            "overpay_caught_eur": round(float(m["overpay_eur"].sum()), 2),
        },
        "rows": recs(m),
    }

# ---- stock & reorder ------------------------------------------------------
@app.get("/api/stock")
def stock():
    rows = []
    for sku, bal in STOCK.items():
        p = PRODUCTS[sku]
        rows.append({"sku": sku, "name": p["name"], "category": p["category"],
                     "ean13": str(p["ean13"]), "balance": bal,
                     "reorder_point": int(p["reorder_point"]), "par_level": int(p["par_level"]),
                     "below_reorder": bal <= int(p["reorder_point"]),
                     "suggest_order": max(int(p["par_level"]) - bal, 0) if bal <= int(p["reorder_point"]) else 0})
    return {"rows": rows, "below_reorder": sum(1 for r in rows if r["below_reorder"])}

@app.get("/api/ledger")
def ledger(sku: str | None = None, limit: int = 100):
    l = DB["stock_ledger"].sort_values("date", ascending=False)
    if sku: l = l[l["sku"] == sku]
    return recs(l.head(limit))

@app.get("/api/pos")
def pos():
    """Purchase orders grouped with their lines — used to match an uploaded invoice."""
    po = DB["purchase_orders"].merge(
        DB["products"][["sku", "name"]], on="sku", how="left")
    out = []
    for po_id, g in po.groupby("po_id"):
        out.append({"po_id": po_id, "vendor": g.iloc[0]["vendor"],
                    "lines": [{"sku": r["sku"], "name": r["name"],
                               "qty_ordered": int(r["qty_ordered"]),
                               "unit_price": float(r["unit_price"])} for _, r in g.iterrows()]})
    return out

# ---- barcode scan ---------------------------------------------------------
@app.post("/api/scan")
def scan(ean: str, qty: int = 1, outlet: str = "Main Bar"):
    """Scan a barcode -> issue stock (decrement). Returns product + new balance + reorder flag."""
    sku = EAN2SKU.get(str(ean).strip())
    if not sku:
        raise HTTPException(404, f"Unknown barcode {ean}")
    STOCK[sku] = max(STOCK[sku] - qty, 0)
    p = PRODUCTS[sku]
    bal = STOCK[sku]; rp = int(p["reorder_point"])
    return {"sku": sku, "name": p["name"], "ean13": str(ean), "issued": qty, "outlet": outlet,
            "balance": bal, "reorder_point": rp, "below_reorder": bal <= rp,
            "suggest_order": max(int(p["par_level"]) - bal, 0) if bal <= rp else 0}

# ---- AI document extraction (real LLM) ------------------------------------
EXTRACT_PROMPT = (
    "You are an accounts-payable assistant. Extract the line items from this supplier "
    "document (invoice or delivery note). Return ONLY a JSON array, no prose, each element: "
    '{"description": str, "quantity": number, "unit_price": number|null}. '
    "If a field is absent, use null. Do not invent values."
)

def extract_line_items(raw: bytes, filename: str, content_type: str = "") -> list:
    """Shared LLM extraction: bytes -> list of {description, quantity, unit_price}.
    Used by both the upload endpoint and the email-poll endpoint."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "ANTHROPIC_API_KEY not configured on the server")
    b64 = base64.standard_b64encode(raw).decode()
    ct, fn = (content_type or "").lower(), (filename or "").lower()
    if "pdf" in ct or fn.endswith(".pdf"):
        block = {"type": "document", "source": {"type": "base64",
                 "media_type": "application/pdf", "data": b64}}
    else:
        media = "image/png" if "png" in ct or fn.endswith(".png") else "image/jpeg"
        block = {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}}
    try:
        from anthropic import Anthropic
        client = Anthropic()
        msg = client.messages.create(
            model=os.getenv("EXTRACT_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=1500,
            messages=[{"role": "user", "content": [block, {"type": "text", "text": EXTRACT_PROMPT}]}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Extraction failed: {e}")


@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    """Upload an invoice/delivery-note image or PDF -> LLM extracts the line items as JSON."""
    raw = await file.read()
    lines = extract_line_items(raw, file.filename, file.content_type or "")
    return {"filename": file.filename, "line_items": lines, "count": len(lines)}


@app.post("/api/email/poll")
def email_poll():
    """Pull NEW invoice attachments from the configured mailbox and extract each.
    Reads IMAP_HOST/IMAP_USER/IMAP_PASSWORD from the environment."""
    host = os.getenv("IMAP_HOST", "imap.gmail.com")
    user, pwd = os.getenv("IMAP_USER"), os.getenv("IMAP_PASSWORD")
    if not (user and pwd):
        raise HTTPException(503, "Mailbox not configured (set IMAP_USER and IMAP_PASSWORD)")
    import imaplib
    from .email_intake import fetch_invoice_attachments
    try:
        items = fetch_invoice_attachments(host, user, pwd, only_unseen=True, mark_seen=True)
    except imaplib.IMAP4.error as e:
        raise HTTPException(502, f"Mailbox login/read failed: {e}")
    out = []
    for it in items:
        lines = extract_line_items(it["content"], it["filename"], "")
        out.append({"filename": it["filename"], "from": it["from"],
                    "subject": it["subject"], "line_items": lines, "count": len(lines)})
    return {"emails": out, "count": len(out)}


# ---- document capture & autonomous 3-way matching -------------------------
@app.post("/api/documents/poll")
def documents_poll():
    """Capture ALL document types from the mailbox (PO / delivery note / invoice), classify,
    extract and store them. Reads only unread mail and marks it read, so each document is captured once; de-dupes as a safety net."""
    host = os.getenv("IMAP_HOST", "imap.gmail.com")
    user, pwd = os.getenv("IMAP_USER"), os.getenv("IMAP_PASSWORD")
    if not (user and pwd):
        raise HTTPException(503, "Mailbox not configured (set IMAP_USER and IMAP_PASSWORD)")
    import imaplib
    from . import documents as docs
    from .email_intake import fetch_invoice_attachments
    try:
        items = fetch_invoice_attachments(host, user, pwd, only_unseen=True, mark_seen=True)
    except imaplib.IMAP4.error as e:
        raise HTTPException(502, f"Mailbox login/read failed: {e}")
    added = docs.ingest(items)
    return {"added": added, **docs.grouped()}

@app.post("/api/documents/upload")
async def documents_upload(file: UploadFile = File(...)):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "AI reading needs ANTHROPIC_API_KEY on the server")
    from . import documents as docs
    content = await file.read()
    docs.ingest_upload(file.filename, content, file.content_type or "")
    return docs.grouped()

_PAGE_CACHE: dict = {}   # (key, n) -> rendered PNG bytes

@app.get("/api/documents/page")
def documents_page(key: str, n: int = 0):
    """Render a document page to PNG (for the interactive magnifier preview)."""
    from . import documents as docs
    item = docs.RAW.get(key)
    if not item:
        raise HTTPException(404, "Document file not available")
    ctype, content = item
    if (ctype or "").startswith("image/"):
        return Response(content=content, media_type=ctype, headers={"Content-Disposition": "inline"})
    ck = (key, n)
    if ck not in _PAGE_CACHE:
        try:
            import fitz
            d = fitz.open(stream=content, filetype="pdf")
            page = d[max(0, min(n, d.page_count - 1))]
            _PAGE_CACHE[ck] = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)).tobytes("png")
        except Exception as e:
            raise HTTPException(500, f"Could not render page: {e}")
    return Response(content=_PAGE_CACHE[ck], media_type="image/png", headers={"Content-Disposition": "inline"})

@app.get("/api/documents/file")
def documents_file(key: str):
    from . import documents as docs
    item = docs.RAW.get(key)
    if not item:
        raise HTTPException(404, "Document file not available")
    ctype, content = item
    return Response(content=content, media_type=ctype, headers={"Content-Disposition": "inline"})

@app.get("/api/accounting")
def accounting_list():
    from . import documents as docs
    return docs.accounting()

@app.post("/api/accounting/post")
def accounting_post(key: str, undo: bool = False):
    from . import documents as docs
    if not docs.mark_posted(key, posted=not undo):
        raise HTTPException(404, "Invoice not found")
    return docs.accounting()

@app.get("/api/receipts")
def receipts_list():
    from . import documents as docs
    return docs.receipts()

@app.post("/api/receipts/count")
async def receipts_count(key: str, request: Request):
    from . import documents as docs
    body = await request.json()
    if not docs.save_count(key, body.get("counts") or {}, body.get("counted_by"), body.get("note")):
        raise HTTPException(404, "Delivery note not found")
    return docs.receipts()

@app.post("/api/receipts/attach")
async def receipts_attach(key: str, file: UploadFile = File(...)):
    from . import documents as docs
    content = await file.read()
    if not docs.attach_receipt(key, file.filename, content, file.content_type or ""):
        raise HTTPException(404, "Delivery note not found")
    return docs.receipts()

@app.post("/api/receipts/archive")
def receipts_archive(key: str, undo: bool = False):
    from . import documents as docs
    if not docs.archive_delivery(key, not undo):
        raise HTTPException(404, "Delivery note not found")
    return docs.receipts()

@app.get("/api/receipts/dispute.pdf")
def receipts_dispute(key: str):
    import re as _re
    from . import documents as docs
    pdf = docs.dispute_pdf(key)
    if pdf is None:
        raise HTTPException(404, "Delivery note not found")
    d = docs.STORE.get(key) or {}
    fn = "dispute-" + (_re.sub(r"[^A-Za-z0-9_-]", "", str(d.get("doc_number") or "BL")) or "BL") + ".pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fn}"'})

@app.get("/api/documents")
def documents_list():
    from . import documents as docs
    return docs.grouped()

@app.post("/api/documents/sample")
def documents_sample():
    from . import documents as docs
    docs.load_sample()
    return docs.grouped()

@app.delete("/api/documents")
def documents_clear():
    from . import documents as docs
    docs.clear()
    return {"cleared": True, **docs.grouped()}


# ---- serve the web cockpit (mounted last so /api/* and /health win) -------
@app.post("/api/accounting/override")
async def accounting_override(key: str, request: Request):
    from . import documents as docs
    try:
        body = await request.json()
    except Exception:
        body = {}
    lines = None
    if isinstance(body, dict) and not body.get("reset"):
        lines = body.get("lines")
    docs.set_acct_overrides(key, lines)
    return docs.accounting()


from fastapi.staticfiles import StaticFiles
WEB = Path(__file__).resolve().parents[1] / "web"
if WEB.exists():
    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
