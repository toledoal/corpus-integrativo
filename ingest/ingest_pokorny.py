#!/usr/bin/env python3
"""Ingiere Pokorny (StarLing/Starostin) → raíces PIE expertas + linaje reflejo→PIE (fuente no-Wiktionary).

De data/lexicon/pokorny/pokorny.jsonl (scrape_pokorny). Cada entrada: raíz PIE (Proto-IE) + glosa + reflejos por
rama. Se ingiere:
  · protoform_hypothesis(model='Pokorny', source_id='pokorny') por cada raíz PIE — inventario PIE experto.
  · form_etymology(reflejo → raíz PIE, source_id='pokorny') donde el reflejo matchee una forma nuestra
    (por lengua mapeada + forma normalizada sin diacríticos). Mejor rendimiento en Latín (mismo alfabeto).

FUENTE EN CUARENTENA: las adiciones de Starostin son CC-BY-NC-ND → source.redistributable=FALSE (PLAN §5). El texto
de Pokorny (1959) es dominio público; el valor añadido no. Se ingiere para uso interno, NO redistribuible.

Uso: .venv/bin/python ingest/ingest_pokorny.py
"""
import json
import os
import re
import unicodedata
from collections import defaultdict
import psycopg
from config import DSN

POK = "/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/data/lexicon/pokorny/pokorny.jsonl"

# campo de reflejo Pokorny → lect nuestro (dónde intentar el match)
FIELD2LECT = {"Latin": "la", "Old Indian": "sa", "Old Greek": "grc", "Germanic": "gem-pro",
              "Baltic": "bat-pro", "Slavic": "sla-pro", "Other Italic": "itc-pro", "Celtic": "cel-pro",
              "Albanian": "sq", "Armenian": "xcl", "Tocharian": "xto", "Hittite": "hit", "Avestan": "ae"}


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.strip("*-–—·. ")


def clean_pie(p):
    """primera variante de la forma PIE reconstruida (Proto-IE puede traer varias separadas por , o ;)."""
    p = re.split(r"[,;]", p or "")[0].strip()
    return p[:120]


def forms_in(field):
    """extrae formas candidatas de un campo de reflejo: tokens antes de un backtick-glosa o coma, letras/marcas."""
    if not field:
        return []
    # quita glosas entre backticks/comillas y paréntesis
    field = re.sub(r"`[^`]*`", " ", field)
    field = re.sub(r"\([^)]*\)", " ", field)
    field = re.sub(r"[«»\"'‘’]", " ", field)
    out = []
    for tok in re.split(r"[\s,;:.|]+", field):
        t = tok.strip("*-–—")
        # token con letras (permite diacríticos), 2-20 chars, no abreviatura con punto final típico
        if 2 <= len(t) <= 20 and re.search(r"[a-zA-Zà-ɏĀ-ɏ]", t):
            out.append(t)
    return out[:8]                                    # tope: primeros tokens (los lemas principales)


def main():
    if not os.path.exists(POK):
        raise SystemExit(f"no existe {POK} — corre scrape_pokorny.py primero")
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("INSERT INTO source(id,citation,url,kind,license,redistributable) "
                "VALUES('pokorny','Pokorny IEW (1959) / Starostin StarLing digitization','https://starlingdb.org',"
                "'reconstrucción','CC-BY-NC-ND-3.0',FALSE) ON CONFLICT(id) DO UPDATE SET redistributable=FALSE")

    # índice de formas por (lect, forma-norm) para el match de reflejos
    cur.execute("SELECT id, lect_id, orthography FROM form WHERE orthography IS NOT NULL")
    have = defaultdict(list)
    for fid, lect, orth in cur.fetchall():
        have[(lect, norm(orth))].append(fid)

    cur.execute("DELETE FROM form_etymology WHERE source_id='pokorny'")
    cur.execute("DELETE FROM protoform_hypothesis WHERE source_id='pokorny'"); conn.commit()

    entries = [json.loads(l) for l in open(POK, encoding="utf-8")]
    print(f"Pokorny: {len(entries):,} entradas")

    ph_rows, fe_rows, seen_fe = [], [], set()
    nroots = 0
    for e in entries:
        pie = clean_pie(e.get("Proto-IE") or e.get("Root"))
        if not pie:
            continue
        gloss = (e.get("Meaning") or e.get("English meaning") or "")[:200]
        # raíz PIE como hipótesis (cognate_set sintético por raíz Pokorny)
        sid = f"pok:{e['n']}"
        ph_rows.append((sid, "ine-pro", "*" + pie.lstrip("*"), "Pokorny", 0.7, "reconstruido", "pokorny"))
        nroots += 1
        # reflejos → arista a la raíz PIE
        for field, lect in FIELD2LECT.items():
            for form in forms_in(e.get(field)):
                for fid in have.get((lect, norm(form)), []):
                    key = (fid, pie)
                    if key in seen_fe:
                        continue
                    seen_fe.add(key)
                    fe_rows.append((fid, "*" + pie.lstrip("*"), "ine-pro", "herencia", "pokorny"))

    # protoform_hypothesis necesita un cognate_set_id existente; creamos sets sintéticos Pokorny
    cur.execute("CREATE TEMP TABLE _pcs(id TEXT) ON COMMIT DROP")
    with cur.copy("COPY cognate_set(id,label,source,family) FROM STDIN") as cp:
        for r in ph_rows:
            cp.write_row((r[0], r[2], "pokorny", "indo-european"))
    with cur.copy("COPY protoform_hypothesis(cognate_set_id,lect_id,form,model,probability,status,source_id) FROM STDIN") as cp:
        for r in ph_rows:
            cp.write_row(r)
    with cur.copy("COPY form_etymology(child_form_id,parent_form,parent_lect,kind,source_id) FROM STDIN") as cp:
        for r in fe_rows:
            cp.write_row(r)
    conn.commit()
    print(f"OK · raíces PIE (Pokorny) = {nroots:,} · aristas reflejo→PIE casadas = {len(fe_rows):,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
