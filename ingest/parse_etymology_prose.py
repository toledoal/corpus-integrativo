#!/usr/bin/env python3
"""Parser de PROSA etimológica → aristas `form_etymology` estructuradas (el linaje que está en texto, no en templates).

96% de las formas Kaikki traen `etymology_text` en prosa ("Inherited from Vulgar Latin ad illās hōrās…") pero solo
~30% tenía linaje estructurado (lo que Wiktionary dio como template). Aquí se lee la CLÁUSULA ETIMOLÓGICA PRINCIPAL
(la primera) y se crea la arista padre: (kind, lengua-padre, forma-padre). Alta precisión: solo dispara cuando la
lengua es un nombre CONOCIDO (gazetteer de lect.name + alias de ancestros); si no, no inventa.

kind: Inherited/From → herencia · Borrowed/borrowing/loan → prestamo. parent_lect es FK → se resuelve a un lect
existente o se crea el ancestro (whitelist). source_id='kaikki-prose' (reversible, distinguible del template).

Idempotente. Uso: .venv/bin/python ingest/parse_etymology_prose.py [lect …]
"""
import re
import sys
import psycopg
from config import DSN

SRC = "kaikki-prose"

# alias Wiktionary → lect id canónico. Los que no existan se crean (nivel indicado) para satisfacer el FK.
ALIASES = {
    "latin": "la", "vulgar latin": "la-vul", "late latin": "la", "medieval latin": "la",
    "ecclesiastical latin": "la", "new latin": "la", "classical latin": "la",
    "ancient greek": "grc", "koine greek": "grc", "byzantine greek": "grc",
    "proto-indo-european": "ine-pro", "proto-italic": "itc-pro", "proto-germanic": "gem-pro",
    "proto-slavic": "sla-pro", "proto-celtic": "cel-pro", "proto-baltic": "bat-pro",
    "proto-indo-iranian": "iir-pro", "proto-iranian": "ira-pro", "proto-indo-aryan": "inc-pro",
    "old french": "fro", "old english": "ang", "old norse": "non", "old high german": "goh",
    "old dutch": "odt", "middle low german": "gml", "frankish": "frk", "anglo-norman": "xno",
    "sanskrit": "sa", "arabic": "ar",
}
# ancestros a CREAR si no existen (id, name, level)
CREATE = {
    "middle english": ("enm", "Middle English", "lengua"),
    "old church slavonic": ("cu", "Old Church Slavonic", "lengua"),
    "gothic": ("got", "Gothic", "lengua"),
    "proto-west germanic": ("gmw-pro", "Proto-West Germanic", "proto_rama"),
    "proto-balto-slavic": ("bsl-pro", "Proto-Balto-Slavic", "proto_rama"),
    "middle french": ("frm", "Middle French", "lengua"),
    "old occitan": ("pro", "Old Occitan", "lengua"),
    "old portuguese": ("roa-opt", "Old Portuguese", "lengua"),
}
TRIG_LOAN = r"(?:borrowed from|borrowing from|loanword from|loaned from|a loan from)"
TRIG_INH = r"(?:inherited from|derived from|from|via)"
# forma-padre: run de caracteres de palabra/marcas/asterisco-guion, hasta 3 tokens; corta en '+' (derivación)
FORM = r"([*\-]?[^\s,.;:()\"“”+]+(?:\s+[*\-]?[^\s,.;:()\"“”+]+){0,2})"


def build_gazetteer(cur):
    """{nombre_lengua_lower: lect_id}. lect.name (nombres reales) + ALIASES + CREATE. Crea ancestros faltantes."""
    cur.execute("SELECT id, name FROM lect WHERE name IS NOT NULL AND name NOT LIKE '%:%' AND id NOT LIKE 'iec\\_%'")
    name2id = {}
    for lid, name in cur.fetchall():
        k = name.strip().lower()
        if len(k) >= 4 and k not in name2id:          # ≥4 letras evita colisiones con fragmentos (bla, aka…)
            name2id[k] = lid
    have = {r[0] for r in cur.execute("SELECT id FROM lect").fetchall()}
    for name, (lid, nm, lvl) in CREATE.items():
        if lid not in have:
            cur.execute("INSERT INTO lect(id,name,level,attested,source_id) VALUES(%s,%s,%s,FALSE,%s) ON CONFLICT(id) DO NOTHING",
                        (lid, nm, lvl, SRC))
            have.add(lid)
        name2id[name] = lid
    for name, lid in ALIASES.items():
        if lid in have:
            name2id[name] = lid
    return name2id


def main():
    want = sys.argv[1:]
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("INSERT INTO source(id,citation,url,kind,license,redistributable) "
                "VALUES(%s,'Wiktionary etymology prose (parsed)','https://kaikki.org','diccionario','CC-BY-SA-3.0',TRUE) "
                "ON CONFLICT(id) DO NOTHING", (SRC,)); conn.commit()
    gaz = build_gazetteer(cur); conn.commit()
    # alternación de nombres, más largos primero (Vulgar Latin antes que Latin)
    names_alt = "|".join(re.escape(n) for n in sorted(gaz, key=len, reverse=True))
    rx_loan = re.compile(rf"\b{TRIG_LOAN}\s+({names_alt})\s+{FORM}", re.I)
    rx_inh = re.compile(rf"\b{TRIG_INH}\s+({names_alt})\s+{FORM}", re.I)
    print(f"gazetteer: {len(gaz)} nombres de lengua")

    cur.execute("DELETE FROM form_etymology WHERE source_id=%s", (SRC,)); conn.commit()

    q = """SELECT f.id, f.etymology_text FROM form f
           WHERE f.source_id='kaikki' AND f.etymology_text IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM form_etymology fe WHERE fe.child_form_id=f.id)"""
    if want:
        q += " AND f.lect_id = ANY(%s)"; cur.execute(q, (want,))
    else:
        cur.execute(q)
    rows = cur.fetchall()
    print(f"formas con prosa y sin linaje: {len(rows):,}")

    edges, seen = [], set()
    for fid, ety in rows:
        head = ety.split("\n", 1)[0][:300]            # primera línea/cláusula = padre inmediato
        m_loan = rx_loan.search(head)
        m_inh = rx_inh.search(head)
        # el que aparezca ANTES en el texto gana (préstamo vs herencia)
        m, kind = None, None
        if m_loan and (not m_inh or m_loan.start() <= m_inh.start()):
            m, kind = m_loan, "prestamo"
        elif m_inh:
            m, kind = m_inh, "herencia"
        if not m:
            continue
        lang = m.group(1).strip().lower()
        pform = re.sub(r"[\s,.;:]+$", "", m.group(2).strip())
        plect = gaz.get(lang)
        if not plect or not pform or len(pform) > 60 or not any(c.isalpha() for c in pform):
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
    print(f"OK · aristas de linaje desde prosa = {len(edges):,}  (source={SRC})")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
