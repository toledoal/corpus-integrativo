#!/usr/bin/env python3
"""Capa CRIPTOLÓGICA — operadores de correspondencia (Δ) entre reflejos cognados + firma `crypto` por forma.

Dentro de cada cognate_set, alineamos (Needleman-Wunsch sobre los símbolos de clase OAS) los esqueletos de
cada PAR de reflejos de lenguas distintas y leemos columna por columna el operador del cifrado:
    a == b        → conservar   (la clase se mantiene)
    a != b (ambas)→ mutar       (sustitución de clase)
    a o b = ∅     → truncar     (elisión/epéntesis)
Agregamos conteos por (from_lect, to_lect, a, b, env) en AMBAS direcciones (consulta dirigida). env = clase vecina
derecha del lado 'from' ('#' al final). Todo Romance ⇒ crosses_macrosystem=false.

`crypto`(por forma): secuencia de clases (feature_vectors JSONB) + self_info = −Σ log2 p(clase) con la distribución
unigrama de clases del propio corpus romance (autoinformación del esqueleto = "peso" del mensaje bajo el cifrado).

Restringido a lects ROMANCE. NO toca Germánico ni Eslavo.

Uso: .venv/bin/python ingest/build_correspondences.py
"""
import json
import math
from collections import defaultdict, Counter
import psycopg
from families import active

from config import DSN
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]
GAP = "∅"


def nw_align(a, b, match=2, mism=-1, gap=-1):
    """Needleman-Wunsch clásico sobre dos listas de símbolos → lista de columnas (x,y) con GAP donde falte."""
    n, m = len(a), len(b)
    D = [[0]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1): D[i][0] = i*gap
    for j in range(1, m+1): D[0][j] = j*gap
    for i in range(1, n+1):
        for j in range(1, m+1):
            s = match if a[i-1] == b[j-1] else mism
            D[i][j] = max(D[i-1][j-1]+s, D[i-1][j]+gap, D[i][j-1]+gap)
    i, j, col = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i-1][j-1] + (match if a[i-1]==b[j-1] else mism):
            col.append((a[i-1], b[j-1])); i -= 1; j -= 1
        elif i > 0 and D[i][j] == D[i-1][j] + gap:
            col.append((a[i-1], GAP)); i -= 1
        else:
            col.append((GAP, b[j-1])); j -= 1
    col.reverse()
    return col


def corr_type(x, y):
    if x == GAP or y == GAP: return "truncar"
    if x == y:              return "conservar"
    return "mutar"


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} ({len(MEMBERS)} lects)")
    # borrado ACOTADO por FAMILIA (etiqueta), no por lect → un lect compartido no se pisa.
    cur.execute("DELETE FROM correspondence WHERE family = %s", (FAM_NAME,))
    cur.execute("DELETE FROM crypto WHERE form_id IN (SELECT id FROM form WHERE lect_id = ANY(%s))", (MEMBERS,))
    conn.commit()

    # unigrama de clases GLOBAL (todas las lenguas) → self_info idempotente sin importar la familia activa.
    # Se agrega en SQL (no carga toda la tabla a memoria): ~7 filas de clase.
    cur.execute("SELECT unnest(string_to_array(code,'·')) AS cls, count(*) "
                "FROM skeleton WHERE code IS NOT NULL AND code<>'' GROUP BY 1")
    unigram = {cls: n for cls, n in cur.fetchall()}
    total = sum(unigram.values())
    logp = {c: -math.log2(n / total) for c, n in unigram.items()}

    # esqueletos por forma DE LA FAMILIA (para construir su crypto y las correspondencias)
    cur.execute("""SELECT sk.form_id, sk.id, f.lect_id, sk.code
                   FROM skeleton sk JOIN form f ON f.id=sk.form_id
                   WHERE f.lect_id = ANY(%s) AND sk.code IS NOT NULL AND sk.code<>''""", (MEMBERS,))
    skel = {}                                   # form_id -> (skeleton_id, lect, [clases])
    for fid, sid, lect, code in cur.fetchall():
        skel[fid] = (sid, lect, code.split("·"))

    # ---- crypto: autoinformación por forma (con logp GLOBAL) ----
    ncry = 0
    with cur.copy("COPY crypto(form_id,skeleton_id,feature_vectors,self_info) FROM STDIN") as cp:
        for fid, (sid, lect, classes) in skel.items():
            si = sum(logp[c] for c in classes)
            cp.write_row((fid, sid, json.dumps({"classes": classes}), round(si, 4)))
            ncry += 1
    conn.commit()

    # ---- correspondencias: alinear pares de reflejos dentro de cada cognate_set DE ESTA FAMILIA ----
    # ORDER BY form_id → el representante "más corto" se elige de forma DETERMINISTA en empates.
    cur.execute("SELECT cm.cognate_set_id, cm.form_id FROM cognate_member cm "
                "JOIN cognate_set cs ON cs.id=cm.cognate_set_id WHERE cs.family=%s ORDER BY cm.form_id", (FAM_NAME,))
    sets = defaultdict(list)
    for cs, fid in cur.fetchall():
        if fid in skel: sets[cs].append(fid)

    # alineamiento NW memoizado por par de códigos (los esqueletos se repiten mucho) + short-circuit a==b
    nw_cache = {}

    def align(ca, cb):
        if ca == cb:
            return [(x, x) for x in ca]                 # idénticos → todo conservar (sin DP)
        key = (tuple(ca), tuple(cb))
        cols = nw_cache.get(key)
        if cols is None:
            cols = nw_cache[key] = nw_align(ca, cb)
        return cols

    # (from,to,a,b,env,type) -> count
    agg = defaultdict(int)
    npairs = 0
    for cs, fids in sets.items():
        # un representante por lect (evita it-vs-it): el de esqueleto más corto (más canónico)
        by_lect = {}
        for fid in fids:
            lect, classes = skel[fid][1], skel[fid][2]
            if lect not in by_lect or len(classes) < len(by_lect[lect][1]):
                by_lect[lect] = (fid, classes)
        lects = list(by_lect)
        for ii in range(len(lects)):
            for jj in range(ii+1, len(lects)):
                la_, ca = by_lect[lects[ii]]; lb_, cb = by_lect[lects[jj]]
                cols = align(ca, cb)
                for k, (x, y) in enumerate(cols):
                    envx = cols[k+1][0] if k+1 < len(cols) else "#"
                    envy = cols[k+1][1] if k+1 < len(cols) else "#"
                    agg[(lects[ii], lects[jj], x, y, envx, corr_type(x, y))] += 1
                    agg[(lects[jj], lects[ii], y, x, envy, corr_type(y, x))] += 1
                npairs += 1

    ncorr = 0
    with cur.copy("COPY correspondence(from_lect,to_lect,a,b,env,count,corr_type,crosses_macrosystem,family) FROM STDIN") as cp:
        for (frm, to, a, b, env, ct), cnt in agg.items():
            cp.write_row((frm, to, a, b, env, cnt, ct, False, FAM_NAME))
            ncorr += 1
    conn.commit()
    print(f"OK · crypto={ncry:,} formas · pares alineados={npairs:,} · correspondencias={ncorr:,} filas")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
