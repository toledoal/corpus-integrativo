#!/usr/bin/env python3
"""Ingesta genérica CLDF → Postgres (Corpus Integrativo).

Loader ÚNICO para todo el ecosistema CLDF (Lexibank, IDS, Grambank, WOLD, CLICS y —cuando salga— Phonobank):
lee un dataset CLDF con pycldf, reconcilia lenguas por GLOTTOCODE y conceptos por CONCEPTICON_ID, y escribe a
NUESTRO esquema normalizado. Ninguna fuente se privilegia: todo entra como alimentador con su `source_id`.

Uso:  .venv/bin/python ingest/cldf_ingest.py <metadata.json> --source lexibank --license CC-BY-4.0 \
        --glottocodes lati1261,stan1288,ital1282,stan1290,port1283,stan1289,roma1327
"""
import argparse, os, sys
import psycopg
from pycldf import Dataset

from config import DSN


def col(row, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata")
    ap.add_argument("--source", required=True)
    ap.add_argument("--license", default=None)
    ap.add_argument("--glottocodes", default="", help="filtro por glottocode (coma-separado); vacío = todos")
    ap.add_argument("--limit-forms", type=int, default=0)
    args = ap.parse_args()
    keep_gc = set(g for g in args.glottocodes.split(",") if g)

    ds = Dataset.from_metadata(args.metadata)
    print(f"CLDF: {ds.module} · {os.path.dirname(args.metadata)}")

    # --- índices en memoria de las tablas CLDF ---
    params = {}     # parameter_id -> (concepticon_id, gloss)
    if "ParameterTable" in ds:
        for r in ds["ParameterTable"]:
            params[r["ID"]] = (col(r, "Concepticon_ID"), col(r, "Name", "Concepticon_Gloss"))

    langs = {}      # language_id -> dict con glottocode/geo/…
    for r in ds["LanguageTable"]:
        gc = col(r, "Glottocode")
        if keep_gc and gc not in keep_gc:
            continue
        langs[r["ID"]] = dict(
            name=col(r, "Name"), glottocode=gc, iso=col(r, "ISO639P3code", "iso"),
            family=col(r, "Family"), subgroup=col(r, "Subgroup"), macroarea=col(r, "Macroarea"),
            lat=col(r, "Latitude"), lon=col(r, "Longitude"))
    if not langs:
        print("!! ninguna lengua tras el filtro de glottocodes"); return
    print(f"lenguas tras filtro: {len(langs)}  (glottocodes: {sorted(set(l['glottocode'] for l in langs.values()))})")

    conn = psycopg.connect(DSN, autocommit=False)
    cur = conn.cursor()

    # --- fuente ---
    cur.execute("INSERT INTO source(id,citation,url,kind,license,redistributable) VALUES(%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT(id) DO UPDATE SET license=EXCLUDED.license",
                (args.source, f"{args.source} (CLDF)", None, "wordlist", args.license,
                 args.license is None or "NC" not in args.license and "ND" not in args.license))

    # --- lects: UNA por glottocode (reconciliación); id = glottocode (o language_id si no hay glottocode) ---
    gc_to_lect = {}
    for lid, l in langs.items():
        lect_id = l["glottocode"] or f"{args.source}:{lid}"
        if lect_id in gc_to_lect:
            continue
        gc_to_lect[lect_id] = lect_id
        macrosys = "indo-europeo" if (l["family"] or "").startswith("Indo") else (l["family"] or None)
        cur.execute(
            "INSERT INTO lect(id,name,level,glottocode,iso639,macrosystem,family,subgroup,macroarea,latitude,longitude,attested,source_id) "
            "VALUES(%s,%s,'lengua',%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s) ON CONFLICT(id) DO NOTHING",
            (lect_id, l["name"], l["glottocode"], l["iso"], macrosys, l["family"], l["subgroup"],
             l["macroarea"], l["lat"], l["lon"], args.source))
    lang_to_lect = {lid: (l["glottocode"] or f"{args.source}:{lid}") for lid, l in langs.items()}
    print(f"lects creados/reconciliados: {len(gc_to_lect)}")

    # --- conceptos: upsert por concepticon_id (crece el backbone); mapa param->concept.id ---
    param_concept = {}
    for pid, (cid, gloss) in params.items():
        if not cid:
            continue
        cur.execute("INSERT INTO concept(concepticon_id,gloss_en) VALUES(%s,%s) "
                    "ON CONFLICT(concepticon_id) DO UPDATE SET gloss_en=COALESCE(concept.gloss_en,EXCLUDED.gloss_en) "
                    "RETURNING id", (cid, gloss))
        param_concept[pid] = cur.fetchone()[0]

    # --- formas + segmentos ---
    nform = nseg = 0
    for r in ds["FormTable"]:
        lid = r["Language_ID"]
        if lid not in langs:
            continue
        fid = f"{args.source}:{r['ID']}"
        segs = r.get("Segments") or []
        concept_id = param_concept.get(r["Parameter_ID"])
        is_loan = str(col(r, "Loan") or "").lower() in ("true", "1", "yes")
        cur.execute(
            "INSERT INTO form(id,lect_id,concept_id,ipa_raw,segments_raw,orthography,is_loan,source_id) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
            (fid, lang_to_lect[lid], concept_id, "".join(segs) if segs else col(r, "Form"),
             list(segs), col(r, "Form", "Value"), is_loan, args.source))
        for i, s in enumerate(segs):
            cur.execute("INSERT INTO segment(form_id,pos,ipa) VALUES(%s,%s,%s)", (fid, i, s))
            nseg += 1
        nform += 1
        if args.limit_forms and nform >= args.limit_forms:
            break
        if nform % 5000 == 0:
            conn.commit(); print(f"  … {nform} formas")

    conn.commit()
    print(f"OK · formas={nform} · segmentos={nseg} · conceptos vinculados={len(param_concept)}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
