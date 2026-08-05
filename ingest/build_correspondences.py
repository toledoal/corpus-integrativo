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
    # borrado ACOTADO a la familia (para que otras familias coexistan)
    cur.execute("DELETE FROM correspondence WHERE from_lect = ANY(%s) OR to_lect = ANY(%s)", (MEMBERS, MEMBERS))
    cur.execute("DELETE FROM crypto WHERE form_id IN (SELECT id FROM form WHERE lect_id = ANY(%s))", (MEMBERS,))
    conn.commit()

    # esqueletos por forma (solo lects de la familia, con código)
    cur.execute("""SELECT sk.form_id, sk.id, f.lect_id, sk.code
                   FROM skeleton sk JOIN form f ON f.id=sk.form_id
                   WHERE f.lect_id = ANY(%s) AND sk.code IS NOT NULL AND sk.code<>''""", (MEMBERS,))
    skel = {}                                   # form_id -> (skeleton_id, lect, [clases])
    unigram = Counter()
    for fid, sid, lect, code in cur.fetchall():
        classes = code.split("·")
        skel[fid] = (sid, lect, classes)
        unigram.update(classes)

    # ---- crypto: autoinformación por forma ----
    total = sum(unigram.values())
    logp = {c: -math.log2(n/total) for c, n in unigram.items()}
    ncry = 0
    for fid, (sid, lect, classes) in skel.items():
        si = sum(logp[c] for c in classes)
        cur.execute("INSERT INTO crypto(form_id,skeleton_id,feature_vectors,self_info) VALUES(%s,%s,%s,%s)",
                    (fid, sid, psycopg.types.json.Json({"classes": classes}), round(si, 4)))
        ncry += 1
        if ncry % 20000 == 0: conn.commit()
    conn.commit()

    # ---- correspondencias: alinear pares de reflejos dentro de cada cognate_set ----
    cur.execute("SELECT cognate_set_id, form_id FROM cognate_member")
    sets = defaultdict(list)
    for cs, fid in cur.fetchall():
        if fid in skel: sets[cs].append(fid)

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
                cols = nw_align(ca, cb)
                for k, (x, y) in enumerate(cols):
                    envx = cols[k+1][0] if k+1 < len(cols) else "#"
                    envy = cols[k+1][1] if k+1 < len(cols) else "#"
                    agg[(lects[ii], lects[jj], x, y, envx, corr_type(x, y))] += 1
                    agg[(lects[jj], lects[ii], y, x, envy, corr_type(y, x))] += 1
                npairs += 1

    ncorr = 0
    for (frm, to, a, b, env, ct), cnt in agg.items():
        cur.execute("""INSERT INTO correspondence(from_lect,to_lect,a,b,env,count,corr_type,crosses_macrosystem)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,false)""", (frm, to, a, b, env, cnt, ct))
        ncorr += 1
        if ncorr % 5000 == 0: conn.commit()
    conn.commit()
    print(f"OK · crypto={ncry:,} formas · pares alineados={npairs:,} · correspondencias={ncorr:,} filas")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
