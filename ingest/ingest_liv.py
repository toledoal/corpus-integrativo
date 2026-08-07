#!/usr/bin/env python3
"""Ingiere LIV² (Lexicon der indogermanischen Verben, Rix et al. 2001) → raíces verbales PIE CON FUENTE ACADÉMICA.

LIV² es el diccionario etimológico de referencia para el verbo PIE. La versión LLOD (proyecto LiLa, CIRCSE) da
~385 pares verbo-latino → raíz-PIE. Es la capa que a Wiktionary le falta: reconstrucción experta citada
(fuente 'liv', ya registrada en la tabla source: "LIV² (LiLa linked data)", CC-BY-SA-4.0).

Se ingiere en DOS lugares del corpus:
  · form_etymology  — arista de linaje (verbo latino → *raíz-PIE, kind='herencia', source_id='liv'). Enriquece el
    grafo genealógico §3 con una fuente académica, no-Wiktionary.
  · protoform_hypothesis — donde el verbo latino ES miembro de un cognate_set, se añade la raíz PIE como hipótesis
    reconstruida con model='LIV²', source_id='liv', probability alta → la "múltiples PIE con fuente" del PLAN §3c
    (compite/co-existe con las reconstrucciones de Kaikki, cada una con su fuente y peso).

Idempotente (borra source_id='liv' antes). Uso: .venv/bin/python ingest/ingest_liv.py
"""
import os
import re
import unicodedata as U
import psycopg
from config import DSN

TTL = os.environ.get("CI_LIV_TTL",
    "/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/ariadne-lex/data/sources/liv/LIV.ttl")


def norm(f):
    f = re.sub(r"^\*+", "", (f or "").strip()).lower()
    f = U.normalize("NFD", f)
    f = "".join(c for c in f if U.category(c) != "Mn")   # quita macrones/diacríticos
    f = f.replace("u", "v") if False else f              # (u/v se maneja aparte al buscar)
    return U.normalize("NFC", f)


def liv_clean(label):
    """Notación LIV → forma PIE canónica (índice de homónimo, incertidumbre, semivocales, palatovelares)."""
    f = U.normalize("NFC", label.strip())
    f = re.sub(r"\{[^}]*\}", "", f)
    f = re.sub(r"^\s*\d+\.", "", f)
    f = f.replace("?", "").strip()
    f = f.replace("u̯", "w").replace("i̯", "y")
    f = f.replace("g̑", "ǵ").replace("k̑", "ḱ")
    f = re.sub(r"\*+", "", f).strip()
    return f


def parse_ttl():
    """Sujeto = línea sin sangría; recoge label/etymology/etymon → pares (verbo_latino, raíz_PIE)."""
    subj, T = None, {}
    pred_re = re.compile(r"\s+(rdfs:label|lemonEty:etymology|lemonEty:etymon)\s+(.+?)\s*[;.]\s*$")
    for line in open(TTL, encoding="utf-8"):
        if line.strip().startswith("@prefix") or not line.strip():
            continue
        if not line[0].isspace():
            subj = line.split(None, 1)[0]
        if subj is None:
            continue
        m = pred_re.search(line)
        if m:
            p, o = m.group(1), m.group(2).strip()
            if o.startswith('"'):
                o = o.strip('"')
            T.setdefault(subj, {})[p] = o
    pairs = []
    for s, d in T.items():
        if "lemonEty:etymology" in d and "rdfs:label" in d:
            et = T.get(d["lemonEty:etymology"], {}).get("lemonEty:etymon")
            root = T.get(et, {}).get("rdfs:label") if et else None
            if root:
                pairs.append((d["rdfs:label"], root))
    return pairs


def main():
    pairs = parse_ttl()
    print(f"LIV²: {len(pairs)} pares verbo-latino → raíz-PIE en el TTL")

    conn = psycopg.connect(DSN); cur = conn.cursor()

    # índice de formas latinas: norm(orth) y variante u<->v → [form_id]
    cur.execute("SELECT id, orthography FROM form WHERE lect_id='la' AND orthography IS NOT NULL")
    la_by_norm = {}
    for fid, orth in cur.fetchall():
        n = norm(orth)
        la_by_norm.setdefault(n, []).append(fid)
        la_by_norm.setdefault(n.replace("v", "u"), []).append(fid)   # cásate con la ortografía clásica de LIV (uir/vir)

    # cognate_sets de los que cada forma latina es miembro (para protoform_hypothesis)
    cur.execute("""SELECT cm.form_id, cm.cognate_set_id FROM cognate_member cm
                   JOIN form f ON f.id=cm.form_id WHERE f.lect_id='la'""")
    la_sets = {}
    for fid, sid in cur.fetchall():
        la_sets.setdefault(fid, []).append(sid)

    # limpiar carga LIV previa
    cur.execute("DELETE FROM form_etymology WHERE source_id='liv'")
    cur.execute("DELETE FROM protoform_hypothesis WHERE source_id='liv'")
    conn.commit()

    fe_rows, ph_rows = [], []
    ph_seen = set()
    matched = 0
    for latin, root in pairs:
        rc = liv_clean(root)
        if not rc:
            continue
        n = norm(latin).replace("u", "v")            # LIV usa 'u' clásica; nuestras formas suelen usar 'v'
        fids = la_by_norm.get(n) or la_by_norm.get(norm(latin))
        if not fids:
            continue
        matched += 1
        pie_form = "*" + rc
        for fid in set(fids):
            fe_rows.append((fid, pie_form, "ine-pro", "herencia", "liv"))
            for sid in la_sets.get(fid, []):
                key = (sid, rc)
                if key in ph_seen:
                    continue
                ph_seen.add(key)
                ph_rows.append((sid, "ine-pro", pie_form, "LIV²", 0.9, "reconstruido", "liv"))

    with cur.copy("COPY form_etymology(child_form_id,parent_form,parent_lect,kind,source_id) FROM STDIN") as cp:
        for r in fe_rows:
            cp.write_row(r)
    with cur.copy("COPY protoform_hypothesis(cognate_set_id,lect_id,form,model,probability,status,source_id) FROM STDIN") as cp:
        for r in ph_rows:
            cp.write_row(r)
    conn.commit()

    print(f"OK · verbos latinos casados con la BD: {matched}/{len(pairs)}")
    print(f"   · form_etymology (linaje la→*PIE, fuente LIV²): {len(fe_rows):,}")
    print(f"   · protoform_hypothesis (PIE sourced sobre cognate_sets): {len(ph_rows):,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
