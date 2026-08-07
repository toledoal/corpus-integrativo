#!/usr/bin/env python3
"""Loader de wordlist CLDF-CSV SIN metadata json (NorthEuraLex y similares) → Postgres.

Igual que cldf_ingest pero leyendo directamente forms.csv/languages.csv/parameters.csv con las columnas CLDF
estándar (ID, Language_ID, Parameter_ID, Form, Segments, Loan; Glottocode; Concepticon_ID). Reconcilia lenguas por
glottocode y conceptos por concepticon_id; cada forma entra con su `source_id`, `concept_id` e `is_loan`.

Uso: .venv/bin/python ingest/ingest_csv_wordlist.py <dir> --source nel --license CC-BY-4.0
"""
import argparse
import csv
import os
import psycopg
from config import DSN

csv.field_size_limit(10_000_000)


def rd(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def g(row, *names):
    for n in names:
        if row.get(n) not in (None, ""):
            return row[n]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--source", required=True)
    ap.add_argument("--license", default=None)
    args = ap.parse_args()

    langs = {r["ID"]: r for r in rd(os.path.join(args.dir, "languages.csv"))}
    params = {r["ID"]: r for r in rd(os.path.join(args.dir, "parameters.csv"))}
    forms = rd(os.path.join(args.dir, "forms.csv"))
    print(f"{args.source}: {len(langs)} lenguas · {len(params)} conceptos · {len(forms):,} formas")

    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("INSERT INTO source(id,citation,url,kind,license,redistributable) VALUES(%s,%s,NULL,'wordlist',%s,%s) "
                "ON CONFLICT(id) DO UPDATE SET license=EXCLUDED.license",
                (args.source, f"{args.source} (CLDF)", args.license, True))

    # lects por glottocode (reconciliación)
    lang_lect = {}
    for lid, l in langs.items():
        gc = g(l, "Glottocode")
        lect_id = gc or f"{args.source}:{lid}"
        lang_lect[lid] = lect_id
        fam = g(l, "Family")
        macro = "indo-europeo" if (fam or "").startswith("Indo") else fam
        cur.execute("INSERT INTO lect(id,name,level,glottocode,iso639,macrosystem,family,subgroup,macroarea,latitude,longitude,attested,source_id) "
                    "VALUES(%s,%s,'lengua',%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s) ON CONFLICT(id) DO NOTHING",
                    (lect_id, g(l, "Name"), gc, g(l, "ISO639P3code", "ISO"), macro, fam, g(l, "SubGroup", "Subgroup"),
                     g(l, "Macroarea"), g(l, "Latitude"), g(l, "Longitude"), args.source))

    # conceptos por concepticon_id
    param_concept = {}
    for pid, p in params.items():
        cid = g(p, "Concepticon_ID")
        if not cid:
            continue
        cur.execute("INSERT INTO concept(concepticon_id,gloss_en) VALUES(%s,%s) "
                    "ON CONFLICT(concepticon_id) DO UPDATE SET gloss_en=COALESCE(concept.gloss_en,EXCLUDED.gloss_en) RETURNING id",
                    (cid, g(p, "Name", "Concepticon_Gloss")))
        param_concept[pid] = cur.fetchone()[0]
    conn.commit()

    # formas (COPY vía staging para velocidad)
    cur.execute("CREATE TEMP TABLE _f(id TEXT,lect_id TEXT,concept_id INT,ipa TEXT,segs TEXT[],orth TEXT,loan BOOL,src TEXT) ON COMMIT DROP")
    n = 0
    with cur.copy("COPY _f(id,lect_id,concept_id,ipa,segs,orth,loan,src) FROM STDIN") as cp:
        for r in forms:
            lid = r.get("Language_ID")
            if lid not in lang_lect:
                continue
            segs = (r.get("Segments") or "").split() or None
            loan = str(g(r, "Loan") or "").lower() in ("true", "1", "yes")
            cp.write_row((f"{args.source}:{r['ID']}", lang_lect[lid], param_concept.get(r.get("Parameter_ID")),
                          g(r, "Form", "Value"), segs, g(r, "Form", "Value"), loan, args.source))
            n += 1
    cur.execute("""INSERT INTO form(id,lect_id,concept_id,ipa_raw,segments_raw,orthography,is_loan,source_id)
                   SELECT id,lect_id,concept_id,ipa,segs,orth,loan,src FROM _f ON CONFLICT(id) DO NOTHING""")
    conn.commit()
    print(f"OK · formas={n:,} · conceptos vinculados={len(param_concept)} · lects={len(set(lang_lect.values()))}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
