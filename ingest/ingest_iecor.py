#!/usr/bin/env python3
"""Ingiere IE-CoR (Indo-European Cognate Relationships) → cognación EXPERTA/ORO, independiente de Kaikki.

IE-CoR (Heggarty et al. 2023, *Science*) es cognación curada a mano por expertos sobre 160 doculectos IE y
170 conceptos básicos (Swadesh-like), con `justification`, marca de `doubt` y método por miembro. Es la fuente
#1 del PLAN §4 para cognación/genealogía y NO depende de Wiktionary — el contrapunto de calidad a la red `cog`.

Se ingiere como **capa propia, namespaced** (no se fusiona de forma frágil con los lects de Kaikki):
  · lects   → id `iec_<glottocode>` , source_id='iecor'  (Spanish de iecor ≠ 'es' de kaikki; ambos coexisten)
  · concepts→ mapeados por concepticon_id a los ya existentes; los que falten se insertan (llena la capa concepto)
  · forms   → id `iec:<source_id>`, source_id='iecor', orthography=source_form, segments_raw=segments
  · cognate_set (source='iecor-gold', family='indo-european') + members con condition_hyp=1 si doubt

Idempotente: borra todo lo source_id='iecor' / source='iecor-gold' antes de recargar. NO toca datos Kaikki.
Uso: .venv/bin/python ingest/ingest_iecor.py
"""
import json
import os
import re
import psycopg
from config import DSN

IECOR = os.environ.get("CI_IECOR_DIR",
    "/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/data/lexicon/iecor")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def main():
    langs = {l["id"]: l for l in json.load(open(f"{IECOR}/languages.json"))}
    concs = {c["id"]: c for c in json.load(open(f"{IECOR}/concepts.json"))}
    forms = {f["id"]: f for f in json.load(open(f"{IECOR}/forms.json"))}
    csets = json.load(open(f"{IECOR}/cognate_sets.json"))
    print(f"iecor: {len(langs)} lenguas · {len(concs)} conceptos · {len(forms):,} formas · {len(csets):,} cognate_sets")

    conn = psycopg.connect(DSN); cur = conn.cursor()

    # limpiar carga previa de iecor (orden por FK)
    cur.execute("DELETE FROM cognate_member cm USING cognate_set cs WHERE cm.cognate_set_id=cs.id AND cs.source='iecor-gold'")
    cur.execute("DELETE FROM cognate_set WHERE source='iecor-gold'")
    cur.execute("DELETE FROM form WHERE source_id='iecor'")
    cur.execute("DELETE FROM lect WHERE source_id='iecor'")
    conn.commit()

    # 1) LECTS (namespaced iec_<glottocode|iso|sourceid>)
    lang_lect = {}
    lect_rows = {}
    for lid, l in langs.items():
        key = l.get("glottocode") or l.get("iso_code") or l.get("source_id")
        lect_id = f"iec_{key}"
        lang_lect[lid] = lect_id
        lect_rows[lect_id] = (lect_id, l.get("name"), "lengua", l.get("glottocode"), l.get("iso_code"),
                              l.get("family"), l.get("subfamily"), l.get("macroarea"),
                              l.get("latitude"), l.get("longitude"), "iecor")
    with cur.copy("COPY lect(id,name,level,glottocode,iso639,family,subgroup,macroarea,latitude,longitude,source_id) FROM STDIN") as cp:
        for r in lect_rows.values():
            cp.write_row(r)

    # 2) CONCEPTS — mapear por concepticon_id a los existentes; insertar los que falten
    cur.execute("SELECT id, concepticon_id FROM concept WHERE concepticon_id IS NOT NULL")
    by_ccid = {cc: cid for cid, cc in cur.fetchall()}
    cur.execute("SELECT COALESCE(max(id),0) FROM concept"); nextid = cur.fetchone()[0] + 1
    conc_map = {}       # iecor concept_id -> concept.id (int)
    new_conc = []
    for cid, c in concs.items():
        cc = c.get("concepticon_id")
        if cc and cc in by_ccid:
            conc_map[cid] = by_ccid[cc]
        else:
            conc_map[cid] = nextid
            new_conc.append((nextid, cc, c.get("gloss"), c.get("concepticon_gloss"),
                             c.get("semantic_field"), c.get("ontological_category"), c.get("concepticon_definition")))
            if cc:
                by_ccid[cc] = nextid
            nextid += 1
    if new_conc:
        with cur.copy("COPY concept(id,concepticon_id,gloss_en,concepticon_gloss,semantic_field,ontological_category,definition) FROM STDIN") as cp:
            for r in new_conc:
                cp.write_row(r)

    # 3) FORMS
    form_id_map = {}    # iecor form_id -> nuestro form.id
    frows = []
    for fid, f in forms.items():
        lect_id = lang_lect.get(f["language_id"])
        conc = conc_map.get(f["concept_id"])
        if not lect_id:
            continue
        our = f"iec:{f['source_id']}"
        form_id_map[fid] = our
        segs = f.get("segments") or None
        frows.append((our, lect_id, conc, f.get("source_form"), segs,
                      bool(f.get("is_loan")), "iecor"))
    with cur.copy("COPY form(id,lect_id,concept_id,orthography,segments_raw,is_loan,source_id) FROM STDIN") as cp:
        for r in frows:
            cp.write_row(r)
    conn.commit()

    # 4) COGNATE SETS + MEMBERS (oro experto)
    set_rows, mem_rows = [], []
    for c in csets:
        members = [m for m in c.get("members", []) if m.get("form_id") in form_id_map]
        if len(members) < 2:                         # cognado real = ≥2 formas atestiguadas
            continue
        sid = f"iecor:{c['id']}"
        label = c.get("root_gloss") or c.get("root_form") or c["id"]
        set_rows.append((sid, label[:200], "iecor-gold", "indo-european"))
        for m in members:
            mem_rows.append((sid, form_id_map[m["form_id"]], 1 if m.get("doubt") else None))
    with cur.copy("COPY cognate_set(id,label,source,family) FROM STDIN") as cp:
        for r in set_rows:
            cp.write_row(r)
    with cur.copy("COPY cognate_member(cognate_set_id,form_id,condition_hyp) FROM STDIN") as cp:
        for r in mem_rows:
            cp.write_row(r)
    conn.commit()

    print(f"OK · lects={len(lect_rows)} · conceptos nuevos={len(new_conc)} · formas={len(frows):,} "
          f"· cognate_sets(oro)={len(set_rows):,} · miembros={len(mem_rows):,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
