#!/usr/bin/env python3
"""Ingiere las plantillas `cog` de Kaikki → red de COGNADOS explícita (la que Wiktionary ya cura).

Cada entrada de Wiktionary lista SUS cognados como plantillas `cog` (techo → pt teto, gl teito, fr toit, it tetto).
El loader principal las SALTABA (solo inh/bor/der). Aquí se rescatan como **una estrella POR ENTRADA**: el conjunto
cognado = {la entrada} ∪ {sus cognados listados}, anclado en la entrada. **NO se fusionan transitivamente entre
entradas** — eso creaba un blob gigante basura (cog A→B, B→C encadenaba palabras no relacionadas). Cada set es la
afirmación discreta de una entrada; se topa a ≤MAXC cognados (páginas-lista fuera).

Complementa la red por-etymon (build_cognates); es más directa y CRUZA familias. NO destructiva.

Uso: .venv/bin/python ingest/ingest_cog.py
"""
import json
import os
import unicodedata
from collections import defaultdict
import psycopg
from config import DSN, KDIR
from families import all_kaikki_files
import normalize

NAME2CODE = all_kaikki_files()
MAXC = 40                                             # cog listados por entrada > esto = página-lista, se salta


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip("*-·. ")


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print("indexando formas de la BD…")
    cur.execute("SELECT id, lect_id, orthography FROM form WHERE orthography IS NOT NULL")
    have = defaultdict(list)
    for fid, lect, orth in cur.fetchall():
        have[(lect, norm(orth))].append(fid)

    cur.execute("DELETE FROM cognate_member cm USING cognate_set cs WHERE cm.cognate_set_id=cs.id AND cs.source='kaikki-cog'")
    cur.execute("DELETE FROM cognate_set WHERE source='kaikki-cog'"); conn.commit()

    set_rows, mem_rows, nent = {}, [], 0
    for fname, code in NAME2CODE.items():
        path = os.path.join(KDIR, f"{fname}.jsonl")
        if not os.path.isfile(path):
            continue
        for line in open(path, encoding="utf-8"):
            e = normalize.kaikki_entry(json.loads(line))
            w = norm(e["word"])
            if not w:
                continue
            # cognados listados por ESTA entrada
            cogs = []
            for t in e["ety_t"]:
                if t.get("n") != "cog":
                    continue
                a = t.get("a") or {}
                cl, cw = a.get("1"), a.get("2")
                if cl and cw and "," not in cl and " " not in cl and norm(cw):
                    cogs.append((cl, norm(cw)))
            if not cogs or len(cogs) > MAXC:
                continue
            # estrella: esta entrada + sus cognados; matchear a formas reales de la BD
            fids, lects = [], set()
            for (lect, cw) in [(code, w)] + cogs:
                for fid in have.get((lect, cw), []):
                    fids.append(fid); lects.add(lect)
            if len(set(fids)) < 2 or len(lects) < 2:  # cognado real = ≥2 formas en ≥2 lenguas
                continue
            sid = f"cog:wiktionary:{code}:{w}"[:200]
            if sid in set_rows:                       # una entrada por (lect,word); no duplicar
                continue
            set_rows[sid] = (sid, f"{code} {w}", "kaikki-cog", "wiktionary")
            for fid in set(fids):
                mem_rows.append((sid, fid))
            nent += 1
        print(f"  · {fname}: {nent:,} entradas con cognados", end="\r")
    print(f"\nentradas con estrella de cognados: {nent:,}")

    with cur.copy("COPY cognate_set(id,label,source,family) FROM STDIN") as cp:
        for r in set_rows.values():
            cp.write_row(r)
    nmem = 0
    with cur.copy("COPY cognate_member(cognate_set_id,form_id) FROM STDIN") as cp:
        for r in mem_rows:
            cp.write_row(r); nmem += 1
    conn.commit()
    print(f"OK · cognate_sets (kaikki-cog) = {len(set_rows):,} · miembros = {nmem:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
