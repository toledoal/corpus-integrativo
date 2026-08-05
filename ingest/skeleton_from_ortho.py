#!/usr/bin/env python3
"""Esqueleto ORTOGRÁFICO — para formas ancestrales/hermanas SIN IPA (Proto-Itálico, Umbro, etc.).

Las lenguas reconstruidas/antiguas de Kaikki no traen pronunciación, pero están en alfabeto latino (romanización ≈
fonémica). Reusamos el MISMO `compute()` del esqueleto IPA, pasándole las LETRAS de la grafía como "segmentos"
(el clasificador de clase ya reconoce p/t/k/c/q/s/l/r/m/n… porque el dict IPA incluye las letras latinas).
Limpieza mínima latina: NFD (quita macrones), minúsculas, se elide la 'h' (muda/débil en latín).

Uso: .venv/bin/python ingest/skeleton_from_ortho.py itc-pro xum
     (sin args → miembros itálicos con formas sin IPA)
"""
import sys
import unicodedata
import psycopg
from recompute_skeleton import compute   # mismo objeto de esqueleto (clases, vocales, CV)

from config import DSN
DEFAULT_LECTS = ["itc-pro", "xum", "osc", "xfa", "spx"]


def ortho_segments(word):
    """grafía → lista de 'segmentos'-letra para compute() (NFD, minúsculas, sin marcas ni 'h')."""
    w = unicodedata.normalize("NFD", (word or "").strip().strip("*-–—·"))
    w = "".join(c for c in w if unicodedata.category(c) != "Mn").lower()
    return [ch for ch in w if ch.isalpha() and ch != "h"]


def main():
    lects = sys.argv[1:] or DEFAULT_LECTS
    conn = psycopg.connect(DSN, autocommit=False); cur = conn.cursor()
    cur.execute("""SELECT id, lect_id, orthography FROM form
                   WHERE source_id='kaikki' AND segments_raw IS NULL AND orthography IS NOT NULL
                     AND lect_id = ANY(%s)""", (lects,))
    rows = cur.fetchall()
    print(f"formas ancestrales sin IPA a esqueletizar (ortográfico): {len(rows):,}  lects={lects}")
    lineage_cache = {}; n = 0
    for fid, lect, ortho in rows:
        segs = ortho_segments(ortho)
        if not segs:
            continue
        cons, code, vowels, cv, compound = compute(segs)
        if not cons and not vowels:
            continue
        lin = None
        if code:
            if code not in lineage_cache:
                cur.execute("INSERT INTO skeleton_lineage(code) VALUES(%s) ON CONFLICT(code) DO UPDATE SET code=EXCLUDED.code RETURNING id", (code,))
                lineage_cache[code] = cur.fetchone()[0]
            lin = lineage_cache[code]
        cur.execute(
            "INSERT INTO skeleton(id,form_id,stage_lect_id,cons_skeleton,core_skeleton,code,skeleton_lineage_id,vowels,cv_template,is_compound) "
            "VALUES(%s,%s,%s,%s,NULL,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET "
            "cons_skeleton=EXCLUDED.cons_skeleton,code=EXCLUDED.code,skeleton_lineage_id=EXCLUDED.skeleton_lineage_id,"
            "vowels=EXCLUDED.vowels,cv_template=EXCLUDED.cv_template,is_compound=EXCLUDED.is_compound",
            (f"SK:{fid}", fid, lect, cons, code, lin, vowels, cv, compound))
        n += 1
    conn.commit()
    print(f"OK · esqueletos ortográficos={n:,} · códigos únicos={len(lineage_cache)}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
