#!/usr/bin/env python3
"""PRUEBA anti-apofenia: ¿los cognate_sets tienen estructura REAL de esqueleto, o son ruido?

Nulo: similitud media de esqueletos de clase DENTRO de cada set (pares de reflejos) vs pares AL AZAR del corpus.
similitud = (columnas idénticas del alineamiento NW) / (longitud del alineamiento) ∈ [0,1].
Si dentro-set >> azar, la agrupación por etymon capta estructura fonológica genuina (no apofenia).

Uso: .venv/bin/python tests/probe_cognates.py
"""
import random
import psycopg

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "ingest"))
from config import DSN


def nw_align(a, b, match=1, mism=0, gap=0):
    n, m = len(a), len(b)
    D = [[0]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for j in range(1, m+1):
            s = match if a[i-1] == b[j-1] else mism
            D[i][j] = max(D[i-1][j-1]+s, D[i-1][j], D[i][j-1])
    return D[n][m]


def sim(a, b):
    if not a or not b:
        return 0.0
    return nw_align(a, b) / max(len(a), len(b))


def main():
    rng = random.Random(20260805)               # semilla fija (reproducible; no Date/rand del entorno)
    conn = psycopg.connect(DSN); cur = conn.cursor()

    # esqueletos por forma (código de clases)
    cur.execute("SELECT form_id, code FROM skeleton WHERE code IS NOT NULL AND code<>''")
    code = {fid: c.split("·") for fid, c in cur.fetchall()}

    # miembros por set (un representante por lect ya no; usamos todos los reflejos con esqueleto)
    cur.execute("SELECT cognate_set_id, form_id FROM cognate_member")
    sets = {}
    for cs, fid in cur.fetchall():
        if fid in code:
            sets.setdefault(cs, []).append(fid)
    sets = {k: v for k, v in sets.items() if len(v) >= 2}

    # muestra de pares DENTRO de set
    within = []
    for cs, fids in rng.sample(list(sets.items()), min(4000, len(sets))):
        a, b = rng.sample(fids, 2)
        within.append(sim(code[a], code[b]))

    # pares AL AZAR (nulo)
    allf = list(code)
    rnd = []
    for _ in range(len(within)):
        a, b = rng.sample(allf, 2)
        rnd.append(sim(code[a], code[b]))

    mw = sum(within)/len(within); mr = sum(rnd)/len(rnd)
    # p empírico: fracción de pares azar que igualan o superan la media dentro-set
    ge = sum(1 for x in rnd if x >= mw)/len(rnd)
    print(f"similitud media DENTRO de cognate_set : {mw:.3f}  (n={len(within)})")
    print(f"similitud media AL AZAR (nulo)        : {mr:.3f}  (n={len(rnd)})")
    print(f"razón dentro/azar                     : {mw/mr:.2f}×")
    print(f"pares-azar ≥ media dentro-set         : {ge:.4f}  (menor = estructura más real)")
    veredicto = "ESTRUCTURA REAL ✔" if mw > 2*mr else "señal débil ⚠️"
    print(f"veredicto: {veredicto}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
