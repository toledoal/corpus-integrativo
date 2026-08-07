#!/usr/bin/env python3
"""Capa COLEXIFICACIÓN GLOBAL (cross-lingüística, estilo CLICS) — red de significado del PLAN §3.

Colexificación = en UNA lengua, una misma forma cubre ≥2 conceptos Concepticon distintos (p.ej. 'lengua' = órgano
e idioma; 'sol'='día'; 'árbol'='madera'). Es la huella diacrónica de la polisemia. Aquí se computa sobre TODAS las
formas con concept_id (IDS + NorthEuraLex + iecor + Lexibank ≈ 597k formas, cientos de lenguas) — no por familia.

Cada colexificación se guarda como (concept_a, concept_b, lect_id). El PESO cross-lingüístico de un par de conceptos
= nº de lenguas que lo colexifican (query/vista sobre esta tabla). Clave de forma normalizada NFC+minúsculas para no
inflar por variantes Unicode. Tope de conceptos-por-forma (MAXC) evita partículas/ruido.

Idempotente: reconstruye TODA la tabla colex (global, autoritativa). Uso: .venv/bin/python ingest/build_colex_global.py
"""
import unicodedata
from collections import defaultdict
from itertools import combinations
import psycopg
from config import DSN

MAXC = 15                                            # forma con >15 conceptos = partícula/ruido → se salta


def norm(s):
    return unicodedata.normalize("NFC", (s or "").strip().lower())


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    bag = defaultdict(set)                           # (lect, forma_norm) -> {concept_id}
    n = 0
    # (a) concepto a nivel FORMA (wordlists IDS/NEL/iecor/lexibank + kaikki inequívocas)
    cur.execute("SELECT lect_id, orthography, concept_id FROM form WHERE concept_id IS NOT NULL AND orthography IS NOT NULL")
    for lect, ortho, cid in cur.fetchall():
        bag[(lect, norm(ortho))].add(cid); n += 1
    # (b) concepto a nivel SENTIDO (polisemia Kaikki: una grafía con varios sentidos → varios conceptos)
    cur.execute("""SELECT f.lect_id, f.orthography, s.concept_id FROM sense s JOIN form f ON f.id=s.form_id
                   WHERE s.concept_id IS NOT NULL AND f.orthography IS NOT NULL""")
    m = 0
    for lect, ortho, cid in cur.fetchall():
        bag[(lect, norm(ortho))].add(cid); m += 1
    print(f"conceptos: nivel-forma {n:,} + nivel-sentido {m:,} · (lengua,forma) únicas: {len(bag):,}")

    rows, seen = [], set()
    skipped = 0
    for (lect, _f), concepts in bag.items():
        if len(concepts) < 2:
            continue
        if len(concepts) > MAXC:                     # forma hiper-polisémica → ruido, fuera (declarado)
            skipped += 1; continue
        for a, b in combinations(sorted(concepts), 2):
            key = (lect, a, b)
            if key in seen:
                continue
            seen.add(key)
            rows.append((a, b, lect))

    cur.execute("TRUNCATE colex")
    with cur.copy("COPY colex(concept_a,concept_b,lect_id) FROM STDIN") as cp:
        for r in rows:
            cp.write_row(r)
    conn.commit()
    npairs = len({(a, b) for a, b, _ in rows})
    print(f"OK · colexificaciones={len(rows):,} · pares-concepto distintos={npairs:,} · formas hiper-polisémicas saltadas={skipped}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
