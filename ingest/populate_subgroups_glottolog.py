#!/usr/bin/env python3
"""Puebla lect.subgroup (RAMA) para TODAS las lenguas IE desde la clasificación de Glottolog.

Fuente: data/lexicon/glottolog/classification.csv (glottolog-cldf, parámetro `classification` = ruta de glottocodes
indo1319/clas1257/…/<lengua>). Cada lengua IE se asigna a UNA rama tradicional según el primer glottocode de rama
presente en su ruta (orden de prioridad: Slavic antes que Balto-Slavic; Romance antes que Italic). Cubre las ~335
lenguas IE del corpus (incluidas las de Lexibank que families.py no tenía). No toca lects sin glottocode
(proto/ancestros conservan su etiqueta de families.py).

Uso: .venv/bin/python ingest/populate_subgroups_glottolog.py
"""
import csv
import os
import psycopg
from config import DSN

csv.field_size_limit(50_000_000)

CLASS = os.environ.get("CI_GLOTTOLOG",
    "/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/data/lexicon/glottolog/classification.csv")

# glottocode de rama → etiqueta, EN ORDEN DE PRIORIDAD (el primero que aparezca en la ruta gana)
BRANCH = [("roma1334", "Romance"), ("germ1287", "Germanic"), ("slav1255", "Slavic"), ("balt1263", "Baltic"),
          ("celt1248", "Celtic"), ("indo1320", "Indo-Iranian"), ("grae1234", "Hellenic"),
          ("arme1241", "Armenian"), ("alba1267", "Albanian"), ("anat1257", "Anatolian"),
          ("tokh1241", "Tocharian"), ("ital1284", "Italic")]


def main():
    # glottocode → conjunto de glottocodes en su ruta (cols: 0=ID 1=Language_ID 2=Parameter_ID 3=Value; sin header)
    paths = {}
    for r in csv.reader(open(CLASS)):
        if len(r) >= 4 and r[2] == "classification":
            paths[r[1]] = set((r[3] or "").split("/"))
    print(f"rutas de clasificación Glottolog: {len(paths):,}")

    def branch(gc):
        p = paths.get(gc)
        if not p:
            return None
        for code, label in BRANCH:
            if code in p:
                return label
        return None

    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("SELECT id, glottocode FROM lect WHERE family='Indo-European' AND glottocode IS NOT NULL")
    upd = []
    for lid, gc in cur.fetchall():
        b = branch(gc)
        if b:
            upd.append((b, lid))
    cur.executemany("UPDATE lect SET subgroup=%s WHERE id=%s", upd)
    conn.commit()
    print(f"OK · lenguas IE con rama asignada = {len(upd)}")
    cur.execute("SELECT subgroup, count(*) FROM lect WHERE family='Indo-European' AND subgroup IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
    for s, n in cur.fetchall():
        print(f"   {s:14s} {n}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
