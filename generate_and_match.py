"""P2P + Inventory demo — synthetic data, real 3-way match logic, stock ledger.
Seed-stable. Domain: hotel F&B procurement & stock. SEPARATE from the Project 5 repo.
"""
import csv, random, datetime as dt
from pathlib import Path
random.seed(42)
OUT = Path("data"); OUT.mkdir(exist_ok=True)

# ---- reference data -------------------------------------------------------
OUTLETS = ["Central Cellar", "Main Bar", "Restaurant", "Rooftop Bar", "Kitchen"]
VENDORS = ["Vins de Moselle SARL","Premium Spirits Lux","Brasserie Nationale",
           "AquaSource SA","Fresh Market Foods","Café & Co"]
# product catalogue: (name, category, unit, vendor, unit_cost, par, reorder_pt)
CATALOG = [
 ("Champagne Brut NV","Wine","bottle","Vins de Moselle SARL",28.0,60,20),
 ("Riesling Grand Cru","Wine","bottle","Vins de Moselle SARL",17.5,90,30),
 ("Pinot Noir Réserve","Wine","bottle","Vins de Moselle SARL",15.0,80,25),
 ("Crémant de Luxembourg","Wine","bottle","Vins de Moselle SARL",12.0,100,35),
 ("Cognac VSOP","Spirits","bottle","Premium Spirits Lux",42.0,24,8),
 ("Single Malt 12y","Spirits","bottle","Premium Spirits Lux",38.0,30,10),
 ("Gin London Dry","Spirits","bottle","Premium Spirits Lux",19.0,40,15),
 ("Vodka Premium","Spirits","bottle","Premium Spirits Lux",17.0,40,15),
 ("Rum Añejo","Spirits","bottle","Premium Spirits Lux",21.0,30,10),
 ("Pils Lager 33cl","Beer","bottle","Brasserie Nationale",0.9,480,150),
 ("IPA Craft 33cl","Beer","bottle","Brasserie Nationale",1.3,240,80),
 ("Still Water 75cl","Soft","bottle","AquaSource SA",0.6,600,200),
 ("Sparkling Water 75cl","Soft","bottle","AquaSource SA",0.7,600,200),
 ("Tonic Water 20cl","Soft","bottle","AquaSource SA",0.5,360,120),
 ("Cola 20cl","Soft","bottle","AquaSource SA",0.45,360,120),
 ("Orange Juice 1L","Soft","carton","Fresh Market Foods",1.8,120,40),
 ("Espresso Beans 1kg","Food","bag","Café & Co",14.0,40,12),
 ("Butter 250g","Food","pack","Fresh Market Foods",1.6,200,60),
 ("Foie Gras 500g","Food","tin","Fresh Market Foods",36.0,30,10),
 ("Smoked Salmon 1kg","Food","pack","Fresh Market Foods",24.0,40,12),
]
def ean13():
    d=[random.randint(0,9) for _ in range(12)]
    chk=(10-((sum(d[0::2])+3*sum(d[1::2]))%10))%10
    return "".join(map(str,d+[chk]))

products=[]
for i,(name,cat,unit,vendor,cost,par,rp) in enumerate(CATALOG,1):
    products.append(dict(sku=f"SKU{i:03d}", name=name, category=cat, unit=unit,
        ean13=ean13(), vendor=vendor, unit_cost=cost, par_level=par, reorder_point=rp,
        home_outlet="Central Cellar"))

# ---- purchase orders, delivery notes, invoices ----------------------------
start=dt.date(2026,1,6)
pos, dn, inv = [], [], []
po_n=dn_n=inv_n=0
by_vendor={v:[p for p in products if p["vendor"]==v] for v in VENDORS}

for week in range(12):
    for vendor in VENDORS:
        if random.random()<0.55:  # not every vendor every week
            continue
        po_n+=1; po_id=f"PO{po_n:04d}"; order_date=start+dt.timedelta(days=week*7+random.randint(0,3))
        items=random.sample(by_vendor[vendor], k=min(len(by_vendor[vendor]),random.randint(2,5)))
        dn_n+=1; dn_id=f"DN{dn_n:04d}"; recv_date=order_date+dt.timedelta(days=random.randint(2,6))
        inv_n+=1; inv_id=f"INV{inv_n:04d}"
        for p in items:
            qty=random.choice([6,12,12,24,24,48])
            po_price=round(p["unit_cost"]*random.uniform(1.0,1.08),2)  # purchase price
            pos.append(dict(po_id=po_id, order_date=order_date, vendor=vendor, sku=p["sku"],
                            qty_ordered=qty, unit_price=po_price))
            # delivery: 88% exact, else short/over/missing
            r=random.random()
            if r<0.06:  # missing line on delivery
                recv=0
            elif r<0.14:  # short delivery
                recv=qty-random.choice([1,2,6])
            elif r<0.18:  # over delivery
                recv=qty+random.choice([1,6])
            else:
                recv=qty
            recv=max(recv,0)
            if recv>0:
                dn.append(dict(dn_id=dn_id, po_id=po_id, recv_date=recv_date, sku=p["sku"],
                               qty_received=recv, qty_ordered_ref=qty,
                               received_by=random.choice(["A. Klein","M. Weber","S. Hoffmann"])))
            # invoice: bills mostly received, sometimes ordered (=> overbill if short), price drift
            billed = qty if random.random()<0.12 else (recv if recv>0 else qty)
            inv_price = po_price if random.random()<0.8 else round(po_price*random.uniform(1.02,1.12),2)
            inv.append(dict(inv_id=inv_id, po_id=po_id, dn_id=dn_id, vendor=vendor, sku=p["sku"],
                            qty_billed=billed, unit_price=inv_price, po_unit_price=po_price))

# ---- 3-WAY MATCH ENGINE ---------------------------------------------------
PRICE_TOL=0.01
def match():
    # index PO and DN by (po_id, sku)
    po_idx={(r["po_id"],r["sku"]):r for r in pos}
    dn_idx={}
    for r in dn: dn_idx[(r["po_id"],r["sku"])]=r
    results=[]
    for r in inv:
        key=(r["po_id"],r["sku"])
        po_r=po_idx.get(key); dn_r=dn_idx.get(key)
        qty_ord=po_r["qty_ordered"] if po_r else None
        qty_recv=dn_r["qty_received"] if dn_r else 0
        qty_bill=r["qty_billed"]
        flags=[]
        if po_r is None: flags.append("NO_PO")
        if dn_r is None: flags.append("NO_DELIVERY")
        if po_r and qty_recv<qty_ord: flags.append("SHORT_DELIVERY")
        if po_r and qty_recv>qty_ord: flags.append("OVER_DELIVERY")
        if qty_bill>qty_recv: flags.append("OVERBILLED")          # billed > delivered = leakage
        if abs(r["unit_price"]-r["po_unit_price"])>PRICE_TOL: flags.append("PRICE_VARIANCE")
        status="MATCHED" if not flags else ("EXCEPTION" if any(f in ("OVERBILLED","NO_PO","NO_DELIVERY","PRICE_VARIANCE") for f in flags) else "REVIEW")
        # € impact of the discrepancy (what we'd overpay if not caught)
        overpay=0.0
        if "OVERBILLED" in flags: overpay+=(qty_bill-qty_recv)*r["unit_price"]
        if "PRICE_VARIANCE" in flags: overpay+=(r["unit_price"]-r["po_unit_price"])*qty_bill
        results.append(dict(inv_id=r["inv_id"], po_id=r["po_id"], dn_id=r["dn_id"], sku=r["sku"],
            vendor=r["vendor"], qty_ordered=qty_ord, qty_received=qty_recv, qty_billed=qty_bill,
            po_unit_price=r["po_unit_price"], inv_unit_price=r["unit_price"],
            status=status, flags="|".join(flags) or "—", overpay_eur=round(overpay,2)))
    return results
matches=match()

# ---- STOCK LEDGER ---------------------------------------------------------
# receipts (+) from delivery notes, then simulate consumption (-) per outlet
stock={p["sku"]:0 for p in products}
ledger=[]
for r in sorted(dn, key=lambda x:x["recv_date"]):
    stock[r["sku"]]+=r["qty_received"]
    ledger.append(dict(date=r["recv_date"], sku=r["sku"], outlet="Central Cellar",
        movement="RECEIPT", qty=r["qty_received"], balance=stock[r["sku"]], ref=r["dn_id"]))
# simulated issues/sales: each SKU consumes a realistic fraction of what was received
for p in products:
    received_total = stock[p["sku"]]
    remaining = int(received_total * random.uniform(0.35, 0.8))
    while remaining > 0:
        q = min(remaining, random.choice([1,2,3,6,6,12]))
        if stock[p["sku"]] - q < 0: break
        stock[p["sku"]] -= q; remaining -= q
        d = start + dt.timedelta(days=random.randint(7,90))
        ledger.append(dict(date=d, sku=p["sku"], outlet=random.choice(OUTLETS[1:]),
            movement="ISSUE", qty=-q, balance=stock[p["sku"]], ref="POS"))
# reorder status
reorder=[]
for p in products:
    bal=stock[p["sku"]]
    reorder.append(dict(sku=p["sku"], name=p["name"], outlet="Central Cellar", balance=bal,
        reorder_point=p["reorder_point"], par_level=p["par_level"],
        suggest_order=max(p["par_level"]-bal,0) if bal<=p["reorder_point"] else 0,
        below_reorder=bal<=p["reorder_point"]))

# ---- write ----------------------------------------------------------------
def w(name, rows):
    if not rows: return
    with open(OUT/name,"w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
w("products.csv",products); w("purchase_orders.csv",pos); w("delivery_notes.csv",dn)
w("invoices.csv",inv); w("three_way_match.csv",matches)
w("stock_ledger.csv",ledger); w("reorder_status.csv",reorder)

# ---- summary --------------------------------------------------------------
tot=len(matches); matched=sum(1 for m in matches if m["status"]=="MATCHED")
exc=sum(1 for m in matches if m["status"]=="EXCEPTION")
overpay=sum(m["overpay_eur"] for m in matches)
ob=sum(1 for m in matches if "OVERBILLED" in m["flags"])
pv=sum(1 for m in matches if "PRICE_VARIANCE" in m["flags"])
sd=sum(1 for m in matches if "SHORT_DELIVERY" in m["flags"])
below=sum(1 for r in reorder if r["below_reorder"])
print(f"Products: {len(products)} | POs: {po_n} | Delivery notes: {dn_n} | Invoices lines: {tot}")
print(f"3-way match: {matched} matched ({matched/tot:.0%}) | {exc} exceptions")
print(f"  flagged -> OVERBILLED {ob} | PRICE_VARIANCE {pv} | SHORT_DELIVERY {sd}")
print(f"  € overbilling/variance CAUGHT before payment: EUR {overpay:,.2f}")
print(f"Stock: {below}/{len(products)} SKUs at/below reorder point")
