#!/usr/bin/env python3
"""Ingiere las plantillas `cog` de Kaikki → red de COGNADOS explícita (la que Wiktionary ya cura).

Cada entrada de Wiktionary lista sus cognados como plantillas `cog` (techo → pt teto, gl teito, fr toit, it tetto).
El loader principal las SALTABA (solo tomaba inh/bor/der). Aquí se rescatan: se juntan todas las aristas de
cognación (entrada ↔ cada cognado listado) de TODOS los archivos, se agrupan por componentes conexos (union-find),
y cada componente con ≥2 formas reales en la BD se vuelve un `cognate_set` (source='kaikki-cog', family='wiktionary').

Es una red de cognados COMPLEMENTARIA a la de etymon (build_cognates): más directa y curada, y CRUZA familias.
NO destructiva: no toca los cognados por-etymon existentes.

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


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip("*-·. ")


class UF:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb: self.p[ra] = rb


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    # lookup: (lect, norm_word) -> [form_id]  (solo lo que existe en la BD)
    print("indexando formas de la BD…")
    cur.execute("SELECT id, lect_id, orthography FROM form WHERE orthography IS NOT NULL")
    have = defaultdict(list)
    for fid, lect, orth in cur.fetchall():
        have[(lect, norm(orth))].append(fid)

    # escanear archivos Kaikki, extraer aristas de cognación (cog)
    uf = UF(); nedges = 0
    for fname, code in NAME2CODE.items():
        path = os.path.join(KDIR, f"{fname}.jsonl")
        if not os.path.isfile(path):
            continue
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            e = normalize.kaikki_entry(d)
            src = (code, norm(e["word"]))
            for t in e["ety_t"]:
                if t.get("n") != "cog":
                    continue
                a = t.get("a") or {}
                cl, cw = a.get("1"), a.get("2")
                if not (cl and cw):
                    continue
                if "," in cl or " " in cl:            # lista de lenguas → saltar (como en el loader)
                    continue
                dst = (cl, norm(cw))
                if dst != src and dst[1]:
                    uf.union(src, dst); nedges += 1
        print(f"  · {fname}: aristas cog acumuladas {nedges:,}", end="\r")
    print(f"\naristas de cognación 'cog': {nedges:,}")

    # componentes conexos → cognate_set (solo los que tienen ≥2 formas reales en ≥2 lects)
    comps = defaultdict(list)
    for node in uf.p:
        comps[uf.find(node)].append(node)

    cur.execute("DELETE FROM cognate_member cm USING cognate_set cs WHERE cm.cognate_set_id=cs.id AND cs.source='kaikki-cog'")
    cur.execute("DELETE FROM cognate_set WHERE source='kaikki-cog'"); conn.commit()

    nset = nmem = 0
    set_rows, mem_rows = [], []
    for root, nodes in comps.items():
        fids, lects = [], set()
        for (lect, w) in nodes:
            for fid in have.get((lect, w), []):
                fids.append(fid); lects.add(lect)
        if len(fids) < 2 or len(lects) < 2:           # cognado real = ≥2 formas en ≥2 lenguas
            continue
        sid = f"cog:wiktionary:{root[0]}:{root[1]}"[:200]
        label = f"{root[0]} {root[1]}"
        set_rows.append((sid, label, "kaikki-cog", "wiktionary"))
        for fid in set(fids):
            mem_rows.append((sid, fid))
        nset += 1
    # dedup set ids (por si truncan)
    seen = {}
    for r in set_rows: seen[r[0]] = r
    with cur.copy("COPY cognate_set(id,label,source,family) FROM STDIN") as cp:
        for r in seen.values(): cp.write_row(r)
    with cur.copy("COPY cognate_member(cognate_set_id,form_id) FROM STDIN") as cp:
        for r in mem_rows:
            if r[0] in seen: cp.write_row(r); nmem += 1
    conn.commit()
    print(f"OK · cognate_sets (kaikki-cog) = {len(seen):,} · miembros = {nmem:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
