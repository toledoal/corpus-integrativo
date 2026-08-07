#!/usr/bin/env python3
"""Mapea glosas → conceptos Concepticon A NIVEL DE SENTIDO (no de forma) — base honesta de las redes de significado.

Cada sentido (sense) tiene UNA glosa = UN significado; se le asigna su concepto Concepticon por coincidencia de
palabra normalizada (alta precisión, no fuzzy). Así una palabra polisémica (foot = 'parte del cuerpo' + 'pagar')
recibe DOS conceptos en sus dos sentidos (FOOT, PAY) — que es justo lo que necesita la colexificación, y evita el
error de asignar un solo concepto arbitrario a la forma.

Normalización de variantes: parte por ;,/ ; quita paréntesis; quita artículo inicial (a/an/the) y 'to '; usa
gloss_en Y concepticon_gloss; SOLO variantes no ambiguas (→ un concepto). NO toca sentidos ya mapeados.
`form.concept_id` se rellena solo si los sentidos de la forma apuntan a UN único concepto (inequívoca); si es
polisémica queda NULL (el significado vive en los sentidos). Respeta form.concept_id de wordlists (IDS/NEL/iecor).

Uso: .venv/bin/python ingest/map_concepticon.py
"""
import re
import psycopg
from collections import defaultdict
from config import DSN

_ART = re.compile(r"^(to |a |an |the )")
_PAR = re.compile(r"\([^)]*\)")


def variants(g):
    out = set()
    for part in re.split(r"[;,/]", (g or "").lower()):
        p = _PAR.sub("", part).strip()
        p = _ART.sub("", p).strip()
        p = re.sub(r"[.\s]+$", "", p).strip()
        if p and 1 <= len(p) <= 40:
            out.add(p)
    return out


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()

    cur.execute("SELECT id, gloss_en, concepticon_gloss FROM concept")
    v2c = defaultdict(set)
    for cid, en, cc in cur.fetchall():
        for g in (en, cc):
            # EXCLUIR conceptos con paréntesis-desambiguador ("SET (HEAVENLY BODIES)", "SHEET (CLASSIFIER)"):
            # quitar el paréntesis daría el match por palabra suelta ("set") a un concepto especializado → falsos.
            if not g or "(" in g:
                continue
            for v in variants(g):
                v2c[v].add(cid)
    lookup = {v: next(iter(cs)) for v, cs in v2c.items() if len(cs) == 1}
    print(f"variantes de concepto no ambiguas: {len(lookup):,}")

    # 1) mapear cada SENTIDO → concepto (la variante más corta que matchee)
    cur.execute("SELECT id, gloss FROM sense WHERE gloss IS NOT NULL AND concept_id IS NULL")
    srows = []
    for sid, gloss in cur.fetchall():
        best = None
        for v in variants(gloss):
            cid = lookup.get(v)
            if cid is not None and (best is None or len(v) < best[0]):
                best = (len(v), cid)
        if best:
            srows.append((sid, best[1]))
    cur.execute("CREATE TEMP TABLE _s(sid INT, cid INT) ON COMMIT DROP")
    with cur.copy("COPY _s(sid, cid) FROM STDIN") as cp:
        for r in srows:
            cp.write_row(r)
    cur.execute("UPDATE sense s SET concept_id=_s.cid FROM _s WHERE s.id=_s.sid")
    conn.commit()
    print(f"OK · sentidos mapeados a concepto = {len(srows):,}")

    # 2) form.concept_id solo si la forma es INEQUÍVOCA (un único concepto en sus sentidos) y aún no tiene
    cur.execute("""UPDATE form f SET concept_id = sub.cid
                   FROM (SELECT form_id, min(concept_id) cid
                         FROM sense WHERE concept_id IS NOT NULL
                         GROUP BY form_id HAVING count(DISTINCT concept_id)=1) sub
                   WHERE f.id=sub.form_id AND f.concept_id IS NULL""")
    conn.commit()
    cur.execute("SELECT count(*) FROM form WHERE concept_id IS NOT NULL")
    print(f"OK · form.concept_id (inequívocas + wordlists) = {cur.fetchone()[0]:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
