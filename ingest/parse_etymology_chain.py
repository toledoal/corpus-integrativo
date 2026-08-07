#!/usr/bin/env python3
"""Parser de CADENA etimológica completa → linaje hasta PIE (cierra el hueco de las 101k formas 'Etymology tree').

Muchas entradas (sobre todo inglés) guardan la etimología como:
  · un ÁRBOL multilínea: cada línea = "Lengua forma" (Proto-Germanic *fadēr / Old English fæder / …), Y
  · una línea final en PROSA con la cadena completa: "Inherited from Middle English …, from … , from PIE *ph₂tḗr".
El loader normal solo veía templates (aquí no hay) y el parser de prosa tomaba solo la PRIMERA cláusula → estas
palabras se quedaban SIN linaje. Aquí se extrae TODA la cadena (nodos del árbol + todos los "from <Lengua> <forma>"),
creando una arista hijo→cada ancestro. Así llegan a PIE. Alta precisión: solo lenguas del gazetteer conocido.

source_id='kaikki-tree'. Idempotente. Uso: .venv/bin/python ingest/parse_etymology_chain.py [lect …]
"""
import re
import sys
import psycopg
from config import DSN
from parse_etymology_prose import build_gazetteer
from resolve_lineage import LECT_ALIAS

SRC = "kaikki-tree"
LOAN = re.compile(r"\b(borrowed from|borrowing from|loanword from)\b", re.I)


def main():
    want = sys.argv[1:]
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("INSERT INTO source(id,citation,url,kind,license,redistributable) "
                "VALUES(%s,'Wiktionary etymology tree/chain (parsed)','https://kaikki.org','diccionario','CC-BY-SA-3.0',TRUE) "
                "ON CONFLICT(id) DO NOTHING", (SRC,)); conn.commit()
    gaz = build_gazetteer(cur); conn.commit()
    names_alt = "|".join(re.escape(n) for n in sorted(gaz, key=len, reverse=True))
    # nodo de árbol: línea "Lengua forma"; cadena en prosa: "from Lengua forma"
    rx_node = re.compile(rf"^\s*({names_alt})\s+([^\s,.;:()\"“”]+(?:\s+[^\s,.;:()\"“”+]+){{0,2}})\s*$")
    rx_chain = re.compile(rf"\b(?:from|inherited from|borrowed from|derived from|via)\s+({names_alt})\s+([*\-]?[^\s,.;:()\"“”+]+)", re.I)
    print(f"gazetteer: {len(gaz)} nombres")

    cur.execute("DELETE FROM form_etymology WHERE source_id=%s", (SRC,)); conn.commit()

    q = """SELECT f.id, f.lect_id, f.etymology_text FROM form f
           WHERE f.source_id='kaikki' AND f.etymology_text IS NOT NULL
             AND (f.etymology_text LIKE 'Etymology tree%%' OR f.etymology_text ~ ', from ')"""
    if want:
        q += " AND f.lect_id = ANY(%s)"; cur.execute(q, (want,))
    else:
        cur.execute(q)
    rows = cur.fetchall()
    print(f"formas con árbol/cadena: {len(rows):,}")

    edges, seen = [], set()
    for fid, lect, ety in rows:
        pairs = []
        for line in ety.split("\n"):
            m = rx_node.match(line)
            if m:
                pairs.append((m.group(1), m.group(2), "herencia"))
        for m in rx_chain.finditer(ety):
            kind = "prestamo" if LOAN.search(ety[max(0, m.start()-20):m.start()]) else "herencia"
            pairs.append((m.group(1), m.group(2), kind))
        for lang, pform, kind in pairs:
            plect = LECT_ALIAS.get(gaz.get(lang.lower()), gaz.get(lang.lower()))
            pform = re.sub(r"[\s,.;:]+$", "", pform.strip())
            if not plect or plect == lect or not pform or len(pform) > 60 or not any(c.isalpha() for c in pform):
                continue
            key = (fid, plect, pform, kind)
            if key in seen:
                continue
            seen.add(key)
            edges.append((fid, pform, plect, kind, SRC))

    with cur.copy("COPY form_etymology(child_form_id,parent_form,parent_lect,kind,source_id) FROM STDIN") as cp:
        for e in edges:
            cp.write_row(e)
    conn.commit()
    print(f"OK · aristas de cadena = {len(edges):,}  (source={SRC})")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
