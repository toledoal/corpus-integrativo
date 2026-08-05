#!/usr/bin/env python3
"""Capa POLYSEME_LINK — red de polisemia intra-lengua: los sentidos de UNA MISMA forma se enlazan entre sí.

Para cada forma romance con ≥2 sentidos, enlazamos sus sentidos (relation='same_form'). Si una forma tiene muchos
sentidos se enlaza en CADENA (consecutivos) para no explotar en C(n,2); con pocos, todos los pares. Es el sustrato
de la polisemia = colexificación diacrónica dentro de la palabra (split/merge/shift se leerán después).

Restringido a lects ROMANCE.

Uso: .venv/bin/python ingest/build_polysemy.py
"""
import psycopg
from itertools import combinations
from families import active

from config import DSN
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]
FULL_PAIRS_MAX = 6            # ≤6 sentidos → todos los pares; más → cadena


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} ({len(MEMBERS)} lects)")
    cur.execute("DELETE FROM polyseme_link WHERE lect_id = ANY(%s)", (MEMBERS,)); conn.commit()

    cur.execute("""SELECT s.form_id, f.lect_id, array_agg(s.id ORDER BY s.id)
                   FROM sense s JOIN form f ON f.id=s.form_id
                   WHERE f.lect_id = ANY(%s)
                   GROUP BY 1,2 HAVING count(*)>1""", (MEMBERS,))
    rows = cur.fetchall()
    print(f"formas romance polisémicas: {len(rows):,}")

    nlink = 0
    with cur.copy("COPY polyseme_link(sense_a,sense_b,lect_id,relation) FROM STDIN") as cp:
        for form_id, lect, sids in rows:
            pairs = combinations(sids, 2) if len(sids) <= FULL_PAIRS_MAX else zip(sids, sids[1:])
            for a, b in pairs:
                cp.write_row((a, b, lect, "same_form"))
                nlink += 1
    conn.commit()
    print(f"OK · enlaces de polisemia={nlink:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
