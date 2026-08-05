#!/usr/bin/env python3
"""Reconciliación de LECTS (paso 1 de la reconciliación) — elimina el Frankenstein de lengua.

Kaikki/seed usan códigos ISO ('la','es'); Lexibank usa glottocodes ('lati1261','stan1288'). La misma lengua vive
como DOS nodos → la misma palabra cae en lects distintos. Aquí: un nodo canónico por lengua, con id legible (ISO) +
`glottocode` como atributo-clave estándar (+ geo de Lexibank). Se fusiona el nodo-glottocode DENTRO del nodo-ISO:
copiar geo/glottocode, repuntar TODAS las referencias, borrar el duplicado.

Uso: .venv/bin/python ingest/reconcile_lects.py
"""
import psycopg
from families import all_reconcile_pairs

from config import DSN
# glottocode (Lexibank, a fusionar/borrar) → id canónico ISO (a conservar) — unión de todas las familias
PAIRS = all_reconcile_pairs()
# columnas que referencian lect(id): (tabla, columna)
REFS = [("form", "lect_id"), ("ancestry_edge", "child_lect"), ("ancestry_edge", "parent_lect"),
        ("protoform_hypothesis", "lect_id"), ("polyseme_link", "lect_id"), ("colex", "lect_id"),
        ("substrate_edge", "source_lect"), ("skeleton", "stage_lect_id"),
        ("correspondence", "from_lect"), ("correspondence", "to_lect"),
        ("affix", "origin_lect"), ("form_etymology", "parent_lect")]


def exists(cur, lid):
    cur.execute("SELECT 1 FROM lect WHERE id=%s", (lid,)); return cur.fetchone() is not None


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    merged = 0
    for glot, iso in PAIRS.items():
        if not exists(cur, glot):
            continue
        if not exists(cur, iso):
            # no hay nodo ISO: crear el canónico copiando el glottocode, repuntar refs, borrar el duplicado.
            # (renombrar el PK directo rompería los FK sin ON UPDATE CASCADE si ya hay dependientes)
            cur.execute("""INSERT INTO lect
                (id,name,level,glottocode,iso639,macrosystem,family,subgroup,macroarea,latitude,longitude,date_lo,date_hi,attested,source_id)
                SELECT %s,name,level,glottocode,iso639,macrosystem,family,subgroup,macroarea,latitude,longitude,date_lo,date_hi,attested,source_id
                FROM lect WHERE id=%s ON CONFLICT (id) DO NOTHING""", (iso, glot))
            for tbl, colm in REFS:
                cur.execute(f"UPDATE {tbl} SET {colm}=%s WHERE {colm}=%s", (iso, glot))
            cur.execute("DELETE FROM lect WHERE id=%s", (glot,))
            conn.commit(); merged += 1; print(f"· creado+repuntado {glot} → {iso}"); continue
        # copiar glottocode + geo del nodo Lexibank al canónico ISO (donde falte)
        cur.execute("""UPDATE lect c SET glottocode=COALESCE(c.glottocode,g.glottocode),
                        iso639=COALESCE(c.iso639,g.iso639), family=COALESCE(c.family,g.family),
                        subgroup=COALESCE(c.subgroup,g.subgroup), macroarea=COALESCE(c.macroarea,g.macroarea),
                        latitude=COALESCE(c.latitude,g.latitude), longitude=COALESCE(c.longitude,g.longitude)
                       FROM lect g WHERE c.id=%s AND g.id=%s""", (iso, glot))
        # repuntar todas las referencias glot → iso
        for tbl, colm in REFS:
            cur.execute(f"UPDATE {tbl} SET {colm}=%s WHERE {colm}=%s", (iso, glot))
        # borrar el nodo duplicado
        cur.execute("DELETE FROM lect WHERE id=%s", (glot,))
        conn.commit(); merged += 1
        print(f"· fusionado {glot} → {iso}")
    # dedup de ancestry_edge que pudo duplicarse tras repuntar
    cur.execute("""DELETE FROM ancestry_edge a USING ancestry_edge b
                   WHERE a.id>b.id AND a.child_lect=b.child_lect AND a.parent_lect=b.parent_lect
                     AND a.kind=b.kind AND coalesce(a.source_id,'')=coalesce(b.source_id,'')""")
    conn.commit()
    print(f"OK · lects fusionados={merged}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
