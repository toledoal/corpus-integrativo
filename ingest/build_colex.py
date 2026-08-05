#!/usr/bin/env python3
"""Capa COLEX — colexificación: dentro de una lengua, una MISMA grafía cubre ≥2 conceptos Concepticon distintos.

Usa las formas con concept_id (provienen de Lexibank). Si en un lect la grafía X mapea a los conceptos c1 y c2,
registramos el par (concept_a,concept_b,lect_id). Es la señal clásica de colexificación (p. ej. 'lengua' = órgano
y idioma). Cobertura limitada por concept_id (solo formas reconciliadas con Lexibank) — declarado.

Restringido a lects ROMANCE.

Uso: .venv/bin/python ingest/build_colex.py
"""
import psycopg
from itertools import combinations
from collections import defaultdict
from families import active

from config import DSN
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} ({len(MEMBERS)} lects)")
    cur.execute("DELETE FROM colex WHERE lect_id = ANY(%s)", (MEMBERS,)); conn.commit()

    cur.execute("""SELECT lect_id, lower(orthography), concept_id FROM form
                   WHERE lect_id = ANY(%s) AND concept_id IS NOT NULL AND orthography IS NOT NULL""", (MEMBERS,))
    bag = defaultdict(set)                       # (lect, grafia) -> {concept_id}
    for lect, ortho, cid in cur.fetchall():
        bag[(lect, ortho)].add(cid)

    seen = set(); ncol = 0
    for (lect, ortho), concepts in bag.items():
        if len(concepts) < 2:
            continue
        for a, b in combinations(sorted(concepts), 2):
            key = (lect, a, b)                    # dedup: mismo par en el mismo lect (varias grafías) una vez
            if key in seen:
                continue
            seen.add(key)
            cur.execute("INSERT INTO colex(concept_a,concept_b,lect_id) VALUES(%s,%s,%s)", (a, b, lect))
            ncol += 1
    conn.commit()
    print(f"OK · colexificaciones={ncol:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
