#!/usr/bin/env python3
"""Resuelve `form_etymology.parent_form` (texto) → `parent_form_id` (entrada real) para poder ENCADENAR el linaje
hasta PIE (§3f "toda la historia de la palabra").

Cada arista dice "hijo → padre (lengua+forma-texto)". Para subir por el grafo hasta PIE hay que ligar ese texto a la
ENTRADA real del ancestro (su fila en `form`), y así seguir SU etimología. El match por igualdad estricta fallaba en
2/3 de los casos (macrones māter/mātēr, diacríticos, multipalabra). Aquí se normaliza quitando diacríticos y, para
etyma multipalabra, se prueban también la cabeza (último token) y el primer token.

NO destructivo: solo rellena parent_form_id donde estaba NULL. Uso: .venv/bin/python ingest/resolve_lineage.py
"""
import re
import unicodedata
from collections import defaultdict
import psycopg
from config import DSN


# variantes de lengua que NO tienen entrada propia → su lengua canónica (donde viven las entradas).
# Las aristas citan p.ej. "Vulgar Latin mātrem" pero el latín está bajo 'la'; sin esto la cadena se rompe.
LECT_ALIAS = {"la-vul": "la", "la-lat": "la", "la-cla": "la", "la-ecc": "la", "la-med": "la",
              "la-eme": "la", "la-new": "la", "la-ren": "la", "la-afr": "la", "VL.": "la", "LL.": "la",
              "fa-cls": "fa", "grc-koi": "grc", "grc-att": "grc", "grc-dor": "grc", "grc-clas": "grc"}


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.strip("*-–—·. ")


def candidates(parent_form):
    """variantes de match para un parent_form: completo, y si es multipalabra la cabeza (último) y el primero."""
    full = norm(parent_form)
    outs = [full]
    if " " in full:
        toks = [t for t in full.split() if t]
        if toks:
            outs.append(toks[-1]); outs.append(toks[0])   # cabeza y primer token
    return [o for o in outs if o]


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    # índice (lect, forma_norm) -> form_id  (una por clave; la más corta = el lema)
    cur.execute("SELECT id, lect_id, orthography FROM form WHERE orthography IS NOT NULL")
    have = {}
    for fid, lect, orth in cur.fetchall():
        k = (lect, norm(orth))
        if k[1] and (k not in have or len(fid) < len(have[k])):
            have[k] = fid
    print(f"índice de formas: {len(have):,} claves (lengua,forma-norm)")

    cur.execute("SELECT id, parent_lect, parent_form FROM form_etymology WHERE parent_form_id IS NULL AND parent_lect IS NOT NULL")
    edges = cur.fetchall()
    upd = []
    for eid, plect, pform in edges:
        pl = LECT_ALIAS.get(plect, plect)             # colapsa variantes (la-vul→la) a donde viven las entradas
        for cand in candidates(pform):
            fid = have.get((pl, cand))
            if fid:
                upd.append((eid, fid)); break
    print(f"aristas sin resolver: {len(edges):,} · nuevas resueltas: {len(upd):,}")

    cur.execute("CREATE TEMP TABLE _r(eid INT, fid TEXT) ON COMMIT DROP")
    with cur.copy("COPY _r(eid, fid) FROM STDIN") as cp:
        for r in upd:
            cp.write_row(r)
    cur.execute("UPDATE form_etymology fe SET parent_form_id=_r.fid FROM _r WHERE fe.id=_r.eid")
    conn.commit()
    cur.execute("SELECT count(*), count(parent_form_id) FROM form_etymology")
    tot, res = cur.fetchone()
    print(f"OK · aristas resueltas ahora = {res:,}/{tot:,} ({100*res//tot}%)")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
