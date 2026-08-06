#!/usr/bin/env python3
"""Redes semánticas de CODERIVADOS cross-familia: mismo etymon (cognados) + MISMO código OAS + MISMO campo semántico.

Método anti-apofenia (no agrupar por código suelto = resonancia azarosa):
  1. COGNACIÓN cross-familia — se sube el grafo de etimología (form_etymology, multi-hop) hasta el etymon
     PROTO más profundo (PIE/proto-rama). Palabras de familias distintas que llegan al MISMO proto-etymon
     son coderivados reales.
  2. CÓDIGO — dentro del grupo se toma el código OAS que comparten reflejos de ≥2 familias (conservación).
  3. CAMPO SEMÁNTICO — se lee de las glosas (uso), no se inventa; se pide solape léxico entre familias.

Reporta grupos que atraviesan GERMÁNICO ↔ ITÁLICO/ROMANCE con código y campo conservados → escribe markdown.

Uso: .venv/bin/python analysis/coderiv_networks.py > docs/coderiv-networks.md
"""
import sys, re, unicodedata
sys.path.insert(0, "ingest")
from collections import defaultdict, Counter
import psycopg
from config import DSN
from families import FAMILIES

PROTO = {"ine-pro", "gem-pro", "itc-pro", "sla-pro", "bat-pro"}
# familia macro de cada lect (germanic vs italic-romance) para exigir cruce
GERM = set(FAMILIES["germanic"]["members"])
ITAL = set(FAMILIES["romance"]["members"]) | set(FAMILIES["italic"]["members"])
def macro(lect):
    if lect in GERM: return "GERM"
    if lect in ITAL: return "ITAL"
    return None
STOP = set("the a an of to and or in on with for from is was be as by at that this his her its their they "
           "one who whom which used esp especially typically person thing action used a an s pl inflection of "
           "form genitive plural singular masculine feminine neuter dative accusative nominative".split())


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip("*- ·/")


def content_words(gloss):
    ws = re.findall(r"[a-zA-Z]{3,}", (gloss or "").lower())
    return [w for w in ws if w not in STOP]


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    # formas con código (solo IE cargado)
    cur.execute("SELECT f.id, f.lect_id, lower(f.orthography), sk.code "
                "FROM form f JOIN skeleton sk ON sk.form_id=f.id WHERE sk.code IS NOT NULL")
    info, rev = {}, defaultdict(list)
    for fid, lect, orth, code in cur.fetchall():
        info[fid] = (lect, orth, code)
        rev[(lect, norm(orth))].append(fid)
    # aristas de etimología palabra→padre
    cur.execute("SELECT child_form_id, parent_lect, parent_form FROM form_etymology WHERE parent_form IS NOT NULL")
    edges = defaultdict(list)
    for c, pl, pf in cur.fetchall():
        edges[c].append((pl, norm(pf)))
    # glosa representativa por forma
    cur.execute("SELECT DISTINCT ON (form_id) form_id, gloss FROM sense WHERE gloss IS NOT NULL ORDER BY form_id, id")
    gloss = dict(cur.fetchall())

    # sube al etymon PROTO más profundo (memoizado, con corte de ciclo y profundidad)
    memo = {}
    def deep(fid, depth=0, seen=None):
        if fid in memo: return memo[fid]
        if seen is None: seen = set()
        if fid in seen or depth > 8 or fid not in edges:
            return None
        seen.add(fid)
        for pl, pf in edges[fid]:                 # ¿arista directa a un proto?
            if pl in PROTO and pf:
                memo[fid] = (pl, pf); return memo[fid]
        for pl, pf in edges[fid]:                 # si no, sigue al padre que resuelva a una forma
            for pid in rev.get((pl, pf), []):
                r = deep(pid, depth + 1, seen)
                if r:
                    memo[fid] = r; return r
        memo[fid] = None; return None

    # agrupa formas por etymon proto profundo
    groups = defaultdict(list)                     # (proto_lect, etymon) -> [form_id]
    for fid in info:
        lect = info[fid][0]
        if macro(lect) is None:
            continue
        et = deep(fid)
        if et:
            groups[et].append(fid)

    # evalúa cada grupo: ¿código compartido entre GERM e ITAL? ¿campo semántico común?
    results = []
    for (plect, etymon), fids in groups.items():
        by_code = defaultdict(list)                # code -> [(lect, orth, gloss, macro)]
        for fid in fids:
            lect, orth, code = info[fid]
            by_code[code].append((lect, orth, gloss.get(fid, ""), macro(lect)))
        for code, members in by_code.items():
            macros = {m[3] for m in members}
            if macros != {"GERM", "ITAL"}:         # exige CRUCE germánico↔itálico con el MISMO código
                continue
            langs = {m[0] for m in members}
            if len(langs) < 3:                     # al menos 3 lenguas distintas comparten código
                continue
            # campo semántico: palabras de contenido comunes a ambas familias
            gw = Counter(); iw = Counter()
            for lect, orth, gl, mc in members:
                (gw if mc == "GERM" else iw).update(set(content_words(gl)))
            shared = [w for w in gw if w in iw]    # solape léxico germánico∩itálico
            if not shared:
                continue
            field = ", ".join(w for w, _ in Counter({w: gw[w] + iw[w] for w in shared}).most_common(4))
            results.append({
                "etymon": f"{plect} *{etymon}", "code": code, "field": field,
                "nlangs": len(langs), "members": sorted(set((m[0], m[1], (m[2] or "")[:45]) for m in members)),
            })
    # ordena por nº de lenguas que comparten código+campo
    results.sort(key=lambda r: (-r["nlangs"], r["etymon"]))

    # ---- markdown ----
    print("# Redes semánticas de coderivados cross-familia\n")
    print("*Palabras que comparten **etymon** (cognados), **código OAS** y **campo semántico**, atravesando "
          "Germánico ↔ Itálico/Romance. Método anti-apofenia: cognación por etymon proto → conservación de código → "
          "campo leído de las glosas (solape léxico germánico∩itálico).*\n")
    print(f"**{len(results)} redes** encontradas (código+campo conservados entre ≥2 familias y ≥3 lenguas).\n")
    for r in results[:60]:
        print(f"## {r['code']}  ·  {r['etymon']}  —  *{r['field']}*")
        print(f"\n{r['nlangs']} lenguas · código **{r['code']}**\n")
        print("| lengua | forma | glosa |")
        print("|---|---|---|")
        for lect, orth, gl in r["members"]:
            print(f"| {lect} | {orth} | {gl} |")
        print()
    conn.close()


if __name__ == "__main__":
    main()
