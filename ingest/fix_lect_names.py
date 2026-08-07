#!/usr/bin/env python3
"""Rellena nombres de lengua faltantes (lect.name = id) con nombres reales. Calidad de datos del corpus.

Fuentes de nombre, por prioridad:
  1. families.py `all_kaikki_files()` — el NOMBRE de archivo Kaikki ES el nombre de la lengua (English→en,
     Proto-West_Germanic→gmw-pro). Cubre todos los lects Kaikki con su nombre propio.
  2. languages.csv de los datasets CLDF (iecor/ids/nel/lexibank) — por glottocode e iso639.
Solo actualiza donde name IS NULL o name=id (no pisa nombres ya buenos).

Uso: .venv/bin/python ingest/fix_lect_names.py
"""
import csv
import os
import psycopg
from config import DSN
from families import all_kaikki_files

csv.field_size_limit(10_000_000)
LEXDIR = "/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/data/lexicon"


def main():
    # 1) code → nombre desde los nombres de archivo Kaikki
    code2name = {}
    for fname, code in all_kaikki_files().items():
        code2name.setdefault(code, fname.replace("_", " "))

    # 2) glottocode/iso → nombre desde languages.csv CLDF
    gc2name, iso2name = {}, {}
    for ds in ("iecor", "ids", "northeuralex", "lexibank"):
        path = os.path.join(LEXDIR, ds, "languages.csv")
        if not os.path.isfile(path):
            continue
        for r in csv.DictReader(open(path, encoding="utf-8")):
            nm = r.get("Name")
            if not nm:
                continue
            gc = r.get("Glottocode")
            iso = r.get("ISO639P3code") or r.get("ISO")
            if gc:
                gc2name.setdefault(gc, nm)
            if iso:
                iso2name.setdefault(iso, nm)

    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("SELECT id, name, glottocode, iso639 FROM lect WHERE name IS NULL OR name=id")
    rows = cur.fetchall()
    upd = []
    for lid, name, gc, iso in rows:
        new = code2name.get(lid) or gc2name.get(gc) or iso2name.get(iso) or (gc2name.get(lid)) or (iso2name.get(lid))
        if new and new != lid:
            upd.append((new, lid))
    cur.executemany("UPDATE lect SET name=%s WHERE id=%s", upd)
    conn.commit()
    print(f"lects sin nombre: {len(rows)} · nombres asignados: {len(upd)} · aún sin nombre: {len(rows)-len(upd)}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
