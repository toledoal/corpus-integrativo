#!/usr/bin/env python3
"""Construye COGNATE_SETS (red de cognación) agrupando formas por su ETYMON compartido (del grafo de etimología).

Cada forma tiene aristas form_etymology (palabra ← forma-padre en lengua-padre). Agrupamos por el etymon:
  - preferir el ancestro LATINO (la, la-vul/lat/med/ecc, + Vulgar/Late) → key = normalize(parent_form);
  - si no, el PROTO (itc-pro, ine-pro);
  - si no, el primer padre.
Las formas con la misma key son cognadas → un cognate_set. La familia *pedestre* (todas ← lat. pedester/pedestrem)
se vuelve UN conjunto. Límite v1: variantes flexivas del etymon (pedester vs pedestrem) pueden partir el set →
mejora futura. NO destructivo respecto a las formas; solo puebla cognate_set/cognate_member.

Uso: .venv/bin/python ingest/build_cognates.py
"""
import unicodedata
import psycopg
from collections import defaultdict, Counter
from families import active

from config import DSN
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]
# niveles de ancestro por prioridad: [(etiqueta, {lects-padre}, clave_canónica), …]
# la clave canónica (primer lect del nivel) unifica variantes: la/la-vul/VL.→'la', proto→'gem-pro', etc.
TIERS = [(lbl, set(lects), lects[0]) for lbl, lects, _status in FAM["ancestors"]]


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")   # quita macrones/diacríticos
    return s.strip("*-·. ")


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} ({len(MEMBERS)} lects)")
    # borrado ACOTADO por FAMILIA (no por lect): un lect compartido (p.ej. 'la' en romance e italic) NO se pisa.
    # CASCADE en cognate_member y protoform_hypothesis limpia lo dependiente.
    cur.execute("DELETE FROM cognate_set WHERE family = %s", (FAM_NAME,))
    conn.commit()

    # solo aristas cuyas HIJAS son de esta familia
    cur.execute("""SELECT fe.child_form_id, fe.parent_lect, fe.parent_form
                   FROM form_etymology fe JOIN form f ON f.id=fe.child_form_id
                   WHERE fe.parent_form IS NOT NULL AND f.lect_id = ANY(%s)""", (MEMBERS,))
    edges = defaultdict(list)                       # child -> [(parent_lect, parent_form)]
    for child, plect, pform in cur.fetchall():
        edges[child].append((plect, pform))

    # abreviaturas Wiktionary → código de variedad
    ABBR = {"VL.": "la-vul", "LL.": "la-lat"}
    GENERIC = {"la", "VL.", "LL."}                  # 'genérico' = no especifica estadio concreto

    def etymon_key(cands):
        """→ (clave_de_set, lect_padre_crudo_que_casó) para poder registrar la VARIEDAD concreta."""
        for _lbl, lects, keypref in TIERS:          # por prioridad de ancestro (familia)
            for pl, pf in cands:
                if pl in lects and norm(pf):
                    return f"{keypref}:{norm(pf)}", pl
        for pl, pf in cands:                        # último recurso: primer padre con forma
            if norm(pf):
                return f"{pl}:{norm(pf)}", pl
        return None, None

    members = defaultdict(list)
    variety = defaultdict(Counter)                  # key -> Counter de variedades concretas (la-vul, la-cla…)
    for child, cands in edges.items():
        k, raw = etymon_key(cands)
        if k:
            members[k].append(child)
            v = ABBR.get(raw, raw)
            if v not in GENERIC:                    # solo cuenta variedades ESPECÍFICAS
                variety[k][v] += 1

    # se borraron los sets de la familia al inicio → inserción fresca vía COPY (sets primero, luego miembros).
    set_rows = {}                                   # setid -> fila (dedup por si trunca a 200)
    mem_rows = []
    for key, forms in members.items():
        if len(forms) < 2:                          # cognate = ≥2 reflejos
            continue
        setid = f"cog:{FAM_NAME}:{key}"[:200]       # familia en la CLAVE → sin colisión entre familias
        lect, form = key.split(":", 1)
        anc = variety[key].most_common(1)[0][0] if variety[key] else lect   # variedad modal, o el genérico
        set_rows[setid] = (setid, f"{lect} *{form}*", "kaikki-etymology", FAM_NAME, anc)
        for fid in forms:
            mem_rows.append((setid, fid))
    with cur.copy("COPY cognate_set(id,label,source,family,ancestor_lect) FROM STDIN") as cp:
        for r in set_rows.values():
            cp.write_row(r)
    with cur.copy("COPY cognate_member(cognate_set_id,form_id) FROM STDIN") as cp:
        for r in mem_rows:
            cp.write_row(r)
    conn.commit()
    print(f"OK · cognate_sets={len(set_rows):,} · miembros={len(mem_rows):,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
