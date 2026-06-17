#!/usr/bin/env python3
"""Build GL imputation lookups from a real GL export (.xlsx).

Usage:  python build_gl_lookups.py path/to/GL.xlsx [path/to/chart_of_accounts.csv]

Writes data/gl_lookups.local.json with your REAL account / analytics codes.
That file is gitignored and is loaded preferentially over the public demo
data/gl_lookups.json — so your real GL never has to enter the repo.
Expected GL columns: 'Compte général', 'POINT DE VENTE', 'SERVICES',
'INVEST / EXPLOITATION', 'Référence tiers'.
"""
import sys, os, json
import pandas as pd

def modal(g, col):
    vc = g[col].dropna().value_counts()
    if not len(vc):
        return None, 0.0
    return vc.index[0], round(float(vc.iloc[0]) / float(vc.sum()), 3)

def main(gl_path, chart_path=None):
    df = pd.read_excel(gl_path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    labels = {}
    if chart_path and os.path.exists(chart_path):
        c = pd.read_csv(chart_path, dtype=str)
        labels = dict(zip(c.iloc[:, 0].astype(str), c.iloc[:, 1].astype(str)))
    exp = df[df["Compte général"].str.startswith("6", na=False)].copy()
    accounts = {}
    for acc in exp["Compte général"].dropna().unique():
        g = exp[exp["Compte général"] == acc]
        srv, sc = modal(g, "SERVICES")
        pos, pc = modal(g, "POINT DE VENTE")
        inv, _ = modal(g, "INVEST / EXPLOITATION")
        a = str(acc)
        flow = "overhead" if (a.startswith("61") or a[:5] in ("60313","60314","60315","60360") or a[:2] in ("62","63","64")) else "goods"
        accounts[a] = {"label": labels.get(a, a),
                       "services": srv, "services_conf": sc,
                       "pos": pos, "pos_conf": pc, "inv_expl": inv or "EXPLOIT", "flow": flow}
    sup = exp[exp["Référence tiers"].notna()]
    supplier_pos = {}
    for s in sup["Référence tiers"].dropna().unique():
        g = sup[sup["Référence tiers"] == s]
        pos, pc = modal(g, "POINT DE VENTE")
        if pos:
            supplier_pos[str(s)] = {"pos": pos, "pos_conf": pc}
    out = {"_note": "LOCAL lookup built from a real GL (real codes). Gitignored.",
           "vat_account": {"account": "42161100", "label": "TVA en amont"},
           "payable_account": {"account": "44111000", "label": "Fournisseurs"},
           "journal": "ACH", "fallback_account": "60380000",
           "pos_options": sorted({v["pos"] for v in accounts.values() if v["pos"]}),
           "services_options": sorted({v["services"] for v in accounts.values() if v["services"]}),
           "inv_options": sorted({v["inv_expl"] for v in accounts.values() if v["inv_expl"]}) or ["EXPLOIT"],
           "accounts": accounts, "supplier_pos": supplier_pos}
    os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/gl_lookups.local.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("Wrote data/gl_lookups.local.json: %d accounts, %d suppliers"
          % (len(accounts), len(supplier_pos)))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python build_gl_lookups.py path/to/GL.xlsx [chart_of_accounts.csv]")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
