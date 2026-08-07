#!/usr/bin/env python3
"""Linaje EXPERTO a PIE desde IE-CoR — usa el `root_form` reconstruido de cada cognate set (fuente no-Kaikki).

Cada cognate set de IE-CoR trae la raíz reconstruida por expertos (root_form = *méh₂tēr, root_language =
Proto-Indo-European) y sus miembros. Aquí, por cada set con raíz reconstruida, se añade una arista de linaje
member → raíz (a la proto-lengua correcta), source_id='iecor'. Así los ~25k forms de iecor alcanzan su proto/PIE
con respaldo experto, sin depender de las etimologías en prosa de Wiktionary.

Idempotente (borra las aristas source_id='iecor' con kind='herencia' antes). Uso: .venv/bin/python ingest/ingest_iecor_lineage.py
"""
import json
import os
import psycopg
from config import DSN

IECOR = os.environ.get("CI_IECOR_DIR",
    "/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/data/lexicon/iecor")

# root_language de iecor → lect de nuestra BD (donde vive/ancla ese proto)
ROOTLECT = {
    "Proto-Indo-European": "ine-pro", "Proto-Germanic": "gem-pro", "Proto-Indo-Iranic": "iir-pro",
    "Proto-Iranic": "ira-pro", "Proto-Italic": "itc-pro", "Proto-Celtic": "cel-pro",
    "Proto-Balto-Slavic": "bsl-pro", "Proto-Slavic": "sla-pro", "Proto-Hellenic": "grk-pro",
    "Latin": "la", "Ancient Greek": "grc", "Sanskrit": "sa",
}


def main():
    forms = {f["id"]: f for f in json.load(open(f"{IECOR}/forms.json"))}
    csets = json.load(open(f"{IECOR}/cognate_sets.json"))
    conn = psycopg.connect(DSN); cur = conn.cursor()

    # ids reales de las formas iecor que existen en la BD
    cur.execute("SELECT id FROM form WHERE source_id='iecor'")
    have = {r[0] for r in cur.fetchall()}

    cur.execute("DELETE FROM form_etymology WHERE source_id='iecor'"); conn.commit()

    rows, seen = [], set()
    for c in csets:
        root = (c.get("root_form") or "").strip()
        plect = ROOTLECT.get(c.get("root_language"))
        if not root or not plect:
            continue
        for m in c.get("members", []):
            f = forms.get(m.get("form_id"))
            if not f:
                continue
            our = f"iec:{f['source_id']}"
            if our not in have:
                continue
            key = (our, plect, root)
            if key in seen:
                continue
            seen.add(key)
            rows.append((our, root[:200], plect, "herencia", "iecor"))

    with cur.copy("COPY form_etymology(child_form_id,parent_form,parent_lect,kind,source_id) FROM STDIN") as cp:
        for r in rows:
            cp.write_row(r)
    conn.commit()
    print(f"OK · aristas de linaje experto (iecor→proto/PIE) = {len(rows):,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
