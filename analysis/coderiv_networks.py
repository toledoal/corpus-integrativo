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
# Ramas macro DERIVADAS del registro (no hardcodeadas): la rama de una familia = su PROTO-RAMA (primer
# ancestro que no sea PIE). romance+italic → itc-pro (misma rama itálica); germanic → gem-pro; slavic → sla-pro.
# Agregar cualquier familia a families.py la incluye AUTOMÁTICAMENTE aquí.
def _branch(cfg):
    for _lbl, lects, _st in cfg["ancestors"]:
        if lects and lects[0] != "ine-pro":
            return lects[0]
    return cfg["ancestors"][0][1][0]
BRANCH_OF, BRANCH_NAME = {}, {"itc-pro": "Itálico", "gem-pro": "Germánico", "sla-pro": "Eslavo",
                             "bat-pro": "Balto-eslavo", "ine-pro": "Indoeuropeo"}
for _fam, _cfg in FAMILIES.items():
    _b = _branch(_cfg)
    for _m in _cfg["members"]:
        BRANCH_OF.setdefault(_m, _b)
def macro(lect):
    return BRANCH_OF.get(lect)
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

    # evalúa cada grupo: ¿código compartido entre ≥2 macro-ramas (derivadas del registro)? ¿campo común?
    results = []
    for (plect, etymon), fids in groups.items():
        by_code = defaultdict(list)                # code -> [(lect, orth, gloss, macro)]
        for fid in fids:
            lect, orth, code = info[fid]
            by_code[code].append((lect, orth, gloss.get(fid, ""), macro(lect)))
        for code, members in by_code.items():
            present = {m[3] for m in members}
            if len(present) < 2:                   # exige CRUCE de ≥2 ramas con el MISMO código
                continue
            langs = {m[0] for m in members}
            if len(langs) < 3:
                continue
            # campo semántico: palabras de contenido por rama; solape en ≥2 ramas
            byfam = defaultdict(Counter)
            for lect, orth, gl, mc in members:
                byfam[mc].update(set(content_words(gl)))
            wordfams = Counter()
            for fam, c in byfam.items():
                for w in c:
                    wordfams[w] += 1
            shared = [w for w, k in wordfams.items() if k >= 2]   # palabra presente en ≥2 ramas
            if not shared:
                continue
            tot = Counter({w: sum(byfam[f][w] for f in byfam) for w in shared})
            field = ", ".join(w for w, _ in tot.most_common(4))
            results.append({
                "etymon": f"{plect} *{etymon}", "code": code, "field": field,
                "nfam": len(present), "families": sorted(BRANCH_NAME.get(f, f) for f in present),
                "nlangs": len(langs), "members": sorted(set((m[0], m[1], (m[2] or "")[:45]) for m in members)),
            })
    # ordena: primero las que abarcan MÁS ramas (las 3 arriba), luego más lenguas
    results.sort(key=lambda r: (-r["nfam"], -r["nlangs"], r["etymon"]))
    tri = [r for r in results if r["nfam"] == 3]

    # ---- markdown ----
    print("# Redes semánticas de coderivados cross-familia (Germánico · Itálico · Eslavo)\n")
    print("*Palabras que comparten **etymon** (cognados), **código OAS** y **campo semántico**, atravesando "
          "las ramas Germánica, Itálica/Romance y Eslava. Método anti-apofenia: cognación por etymon proto → "
          "conservación de código → campo leído de las glosas (palabra de contenido presente en ≥2 ramas).*\n")
    print(f"**{len(results)} redes** (código+campo en ≥2 ramas, ≥3 lenguas) — de ellas **{len(tri)} abarcan "
          f"las TRES ramas** (Germánico + Itálico + Eslavo).\n")
    for r in results[:70]:
        star = " ⭐ 3 ramas" if r["nfam"] == 3 else ""
        print(f"## {r['code']}  ·  {r['etymon']}  —  *{r['field']}*{star}")
        print(f"\n{r['nlangs']} lenguas · {', '.join(r['families'])} · código **{r['code']}**\n")
        print("| lengua | forma | glosa |")
        print("|---|---|---|")
        for lect, orth, gl in r["members"]:
            print(f"| {lect} | {orth} | {gl} |")
        print()
    conn.close()


if __name__ == "__main__":
    main()
