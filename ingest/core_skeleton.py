#!/usr/bin/env python3
"""Deriva el CORE_SKELETON (raíz sin afijos) pelando la descomposición morfológica de Kaikki.

Fiable, no por coincidencia ortográfica: usa la descomposición que Kaikki YA da en la etimología
('From angosto + -ura', 'sub- + marino'). Regla: **core(palabra) = esqueleto de la BASE** (recursivo un nivel).
Ej.: angostura ← angosto + -ura  →  core(angostura) = cons_skeleton(angosto) = n·g·s·t.
Registra la morfología en `morph` (root→base, affix). Donde no hay descomposición, core queda NULL (honesto).

Uso: .venv/bin/python ingest/core_skeleton.py
"""
import re
import psycopg

from config import DSN
# 'base + -sufijo'  |  'prefijo- + base'
RE_SUF = re.compile(r"([A-Za-zÀ-ÿ]{2,})\s*\+\s*‎?\s*(-[A-Za-zÀ-ÿ]{1,})")
RE_PRE = re.compile(r"([A-Za-zÀ-ÿ]{1,}-)\s*\+\s*‎?\s*([A-Za-zÀ-ÿ]{2,})")


def parse_decomp(ety):
    if not ety or "+" not in ety:
        return None
    m = RE_SUF.search(ety)
    if m:
        return ("suffix", m.group(1).lower(), m.group(2).lower())   # (tipo, base, afijo)
    m = RE_PRE.search(ety)
    if m:
        return ("prefix", m.group(2).lower(), m.group(1).lower())
    return None


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("DELETE FROM morph"); conn.commit()      # idempotente
    # índice: (lect, orthography) → cons_skeleton (para buscar la base)
    cur.execute("""SELECT f.lect_id, lower(f.orthography), sk.cons_skeleton
                   FROM form f JOIN skeleton sk ON sk.form_id=f.id
                   WHERE f.orthography IS NOT NULL AND sk.cons_skeleton IS NOT NULL""")
    skel_of = {}
    for lect, orth, cons in cur.fetchall():
        skel_of.setdefault((lect, orth), cons)

    cur.execute("""SELECT f.id, f.lect_id, lower(f.orthography), f.etymology_text
                   FROM form f JOIN skeleton sk ON sk.form_id=f.id
                   WHERE f.etymology_text IS NOT NULL AND sk.cons_skeleton IS NOT NULL""")
    forms = cur.fetchall()
    print(f"formas con etimología y esqueleto: {len(forms):,}")

    ncore = nmorph = 0
    for fid, lect, orth, ety in forms:
        d = parse_decomp(ety)
        if not d:
            continue
        typ, base, affix = d
        core = skel_of.get((lect, base))
        if not core:
            continue                              # la base no está / sin esqueleto → no forzamos
        cur.execute("UPDATE skeleton SET core_skeleton=%s WHERE form_id=%s", (core, fid))
        ncore += 1
        # morfología: raíz (base) + afijo
        aid = f"afx:{lect}:{affix}"
        cur.execute("SELECT 1 FROM affix WHERE id=%s", (aid,))
        has_affix = cur.fetchone() is not None
        cur.execute("INSERT INTO morph(form_id,role,gloss,affix_id) VALUES(%s,'root',%s,NULL)", (fid, base))
        cur.execute("INSERT INTO morph(form_id,role,gloss,affix_id) VALUES(%s,'affix',%s,%s)",
                    (fid, affix, aid if has_affix else None))   # role='affix' (el tipo pre/suf vive en affix.type)
        nmorph += 2
        if ncore % 3000 == 0:
            conn.commit(); print(f"  … {ncore} cores")
    conn.commit()
    print(f"OK · core_skeleton poblados={ncore:,} · morfemas registrados={nmorph:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
