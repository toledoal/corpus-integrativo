#!/usr/bin/env python3
"""Reconciliación de FORMAS (paso 2) — funde las capas de la misma palabra en un nodo canónico, NO destructivo.

Kaikki es primario (tiene POS + etimología + sentidos). Enriquecemos la forma Kaikki con lo de Lexibank
(segmentos + concepto → le da esqueleto). Emparejamos por (lengua, grafía); elegimos el POS Kaikki que mejor cuadre
con la categoría ontológica del concepto Lexibank (Property→adj, Person/Thing→noun, Action/Process→verb). La forma
Lexibank queda con `superseded_by` = canónica (procedencia intacta, reversible). Homónimos separados por POS.

Uso: .venv/bin/python ingest/reconcile_forms.py
"""
import psycopg
from collections import defaultdict

from config import DSN
ONT2POS = {"Person/Thing": "noun", "Property": "adj", "Action/Process": "verb",
           "Number": "num", "Other": None}
POS_ALIAS = {"adj": {"adj", "adjective"}, "noun": {"noun"}, "verb": {"verb"}, "num": {"num", "numeral"}}


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("ALTER TABLE form ADD COLUMN IF NOT EXISTS pos TEXT, ADD COLUMN IF NOT EXISTS superseded_by TEXT")
    conn.commit()
    # POS de las formas Kaikki (del id: kaikki:code:word:pos) — barato en Python
    cur.execute("SELECT id, lect_id, lower(orthography) FROM form WHERE source_id='kaikki' AND orthography IS NOT NULL")
    kaikki_idx = defaultdict(list)               # (lect, orth) -> [(id, pos)]
    for fid, lect, orth in cur.fetchall():
        pos = fid.rsplit(":", 1)[-1]
        kaikki_idx[(lect, orth)].append((fid, pos))
        cur.execute("UPDATE form SET pos=%s WHERE id=%s", (pos, fid))
    conn.commit()
    print(f"formas Kaikki indexadas: {sum(len(v) for v in kaikki_idx.values())}")

    # formas Lexibank con su categoría ontológica de concepto (para inferir POS)
    cur.execute("""SELECT f.id, f.lect_id, lower(f.orthography), f.segments_raw, f.concept_id, c.ontological_category
                   FROM form f LEFT JOIN concept c ON c.id=f.concept_id
                   WHERE f.source_id='lexibank' AND f.orthography IS NOT NULL""")
    lex = cur.fetchall()
    matched = enriched = 0
    for fid, lect, orth, segs, cid, ont in lex:
        cands = kaikki_idx.get((lect, orth))
        if not cands:
            continue
        matched += 1
        target = ONT2POS.get(ont)
        alias = POS_ALIAS.get(target, set())
        canon = next((kid for kid, p in cands if p in alias), None) or \
                next((kid for kid, p in cands if p == "noun"), None) or cands[0][0]
        # enriquecer la canónica Kaikki con segmentos + concepto Lexibank (si le faltan)
        cur.execute("UPDATE form SET segments_raw=COALESCE(segments_raw,%s), concept_id=COALESCE(concept_id,%s) "
                    "WHERE id=%s AND segments_raw IS NULL", (segs, cid, canon))
        if cur.rowcount:
            enriched += 1
        cur.execute("UPDATE form SET superseded_by=%s WHERE id=%s", (canon, fid))
    conn.commit()
    print(f"OK · formas Lexibank emparejadas con Kaikki={matched} · canónicas enriquecidas (segmentos)={enriched}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
