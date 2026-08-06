#!/usr/bin/env python3
"""Loader de Kaikki (Wiktionary) → Postgres. Fuente PRIMARIA de etimología + sentidos + morfología (Fase 0).

Kaikki NO es CLDF (JSONL por lengua) → loader propio. Por cada palabra extrae:
  - forma (kaikki:<lang>:<word>:<pos>) + IPA + ortografía.
  - SENTIDOS (gloss[]) → tabla `sense` (red polisémica; pie tiene 6 sentidos).
  - ETIMOLOGÍA (ety_t: inh/bor/der) → grafo de linaje: aristas de LENGUA (`ancestry_edge`, dedup) + de PALABRA
    (`form_etymology`, word→word: "toda la historia de la palabra"), con protoformas (itc-pro=Proto-Itálico,
    ine-pro=PIE…) marcadas reconstruidas.
Licencia: Kaikki = CC BY-SA (Wiktionary). Kaikki no trae Concepticon → gloss→Concepticon queda como TODO (puente iecor/IDS).

Uso: .venv/bin/python ingest/kaikki_ingest.py Latin Spanish --limit 0   (0 = sin límite; procesa solo con ety_t)
"""
import argparse, json, os, sys
import psycopg

from config import DSN
from config import KDIR

# código Wiktionary → (nombre, nivel, atestiguado, macrosistema)
LANGMAP = {
    "la": ("Latin", "lengua", True, "indo-europeo"), "es": ("Spanish", "lengua", True, "indo-europeo"),
    "osp": ("Old Spanish", "lengua", True, "indo-europeo"), "it": ("Italian", "lengua", True, "indo-europeo"),
    "fr": ("French", "lengua", True, "indo-europeo"), "pt": ("Portuguese", "lengua", True, "indo-europeo"),
    "ca": ("Catalan", "lengua", True, "indo-europeo"), "ro": ("Romanian", "lengua", True, "indo-europeo"),
    "roa-opt": ("Old Portuguese", "lengua", True, "indo-europeo"), "fro": ("Old French", "lengua", True, "indo-europeo"),
    "la-vul": ("Vulgar Latin", "lengua", False, "indo-europeo"), "la-lat": ("Late Latin", "lengua", True, "indo-europeo"),
    "la-med": ("Medieval Latin", "lengua", True, "indo-europeo"), "la-ecc": ("Ecclesiastical Latin", "lengua", True, "indo-europeo"),
    "itc-pro": ("Proto-Italic", "proto_rama", False, "indo-europeo"),
    "ine-pro": ("Proto-Indo-European", "pie", False, "indo-europeo"),
    "gem-pro": ("Proto-Germanic", "proto_rama", False, "indo-europeo"),
    "sla-pro": ("Proto-Slavic", "proto_rama", False, "indo-europeo"),
    "oc": ("Occitan", "lengua", True, "indo-europeo"), "sc": ("Sardinian", "lengua", True, "indo-europeo"),
    "scn": ("Sicilian", "lengua", True, "indo-europeo"), "nap": ("Neapolitan", "lengua", True, "indo-europeo"),
    "gl": ("Galician", "lengua", True, "indo-europeo"), "rup": ("Aromanian", "lengua", True, "indo-europeo"),
    "fur": ("Friulian", "lengua", True, "indo-europeo"), "lld": ("Ladin", "lengua", True, "indo-europeo"),
    "wa": ("Walloon", "lengua", True, "indo-europeo"), "osp": ("Old Spanish", "lengua", True, "indo-europeo"),
    "grc": ("Ancient Greek", "lengua", True, "indo-europeo"), "ar": ("Arabic", "lengua", True, "semitico"),
    "xcl": ("Classical Arabic", "lengua", True, "semitico"), "he": ("Hebrew", "lengua", True, "semitico"),
    "VL.": ("Vulgar Latin", "lengua", False, "indo-europeo"), "LL.": ("Late Latin", "lengua", True, "indo-europeo"),
}
KIND = {"inh": "herencia", "inh+": "herencia", "bor": "prestamo", "bor+": "prestamo",
        "der": "herencia", "der+": "herencia", "lbor": "prestamo", "slbor": "prestamo"}
from families import all_kaikki_files
NAME2CODE = all_kaikki_files()   # unión de TODAS las familias definidas (mapea el archivo que se cargue)


def lect_meta(code):
    if code in LANGMAP:
        return LANGMAP[code]
    lvl = "proto_rama" if code.endswith("-pro") else "lengua"
    return (code, lvl, not code.endswith("-pro"), "indo-europeo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("languages", nargs="+")           # nombres de archivo Kaikki: Latin Spanish …
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true",     # cargar TODA entrada aunque no traiga etimología
                    help="para lenguas ancestro/hermana (proto, sabélicas) donde el valor es la FORMA, no su ety")
    args = ap.parse_args()

    conn = psycopg.connect(DSN, autocommit=False); cur = conn.cursor()
    # códigos de lect que se van a (re)cargar → borrado INCREMENTAL acotado a ellos (no toca otras lenguas)
    codes = sorted({NAME2CODE.get(l, l.lower()) for l in args.languages})
    print(f"recarga incremental de códigos: {codes}")
    famforms = "SELECT id FROM form WHERE source_id='kaikki' AND lect_id = ANY(%s)"
    # 1) dependencias NO-CASCADE que apuntan a esas formas (borrar antes que la forma)
    cur.execute(f"DELETE FROM form_etymology WHERE child_form_id IN ({famforms})", (codes,))
    cur.execute(f"DELETE FROM cognate_member WHERE form_id IN ({famforms})", (codes,))
    cur.execute(f"DELETE FROM cohort_member  WHERE form_id IN ({famforms})", (codes,))
    cur.execute(f"DELETE FROM substrate_edge WHERE form_id IN ({famforms})", (codes,))
    cur.execute("DELETE FROM ancestry_edge WHERE source_id='kaikki' AND child_lect = ANY(%s)", (codes,))
    # 2) las formas (cascada borra crypto/morph/segment/sense/skeleton de esas formas)
    cur.execute("DELETE FROM form WHERE source_id='kaikki' AND lect_id = ANY(%s)", (codes,))
    conn.commit()
    cur.execute("INSERT INTO source(id,citation,url,kind,license,redistributable) "
                "VALUES('kaikki','Wiktionary via Kaikki/wiktextract','https://kaikki.org','diccionario','CC-BY-SA-3.0',TRUE) "
                "ON CONFLICT(id) DO NOTHING")
    lect_seen = set(); edge_seen = set()

    def ensure_lect(code):
        if code in lect_seen:
            return
        name, lvl, att, ms = lect_meta(code)
        cur.execute("INSERT INTO lect(id,name,level,macrosystem,attested,source_id) VALUES(%s,%s,%s,%s,%s,'kaikki') "
                    "ON CONFLICT(id) DO NOTHING", (code, name, lvl, ms, att))
        lect_seen.add(code)

    def edge(child, parent, kind):
        if child == parent:            # derivación intra-lengua: no es arista de LENGUA (sí de palabra)
            return
        _, _, _, msc = lect_meta(child); _, plvl, _, msp = lect_meta(parent)
        key = (child, parent, kind)
        if key in edge_seen:
            return
        edge_seen.add(key)
        status = "reconstruido" if plvl in ("proto_rama", "pie") else "atestiguado"
        cur.execute("INSERT INTO ancestry_edge(child_lect,parent_lect,kind,status,crosses_macrosystem,source_id) "
                    "VALUES(%s,%s,%s,%s,%s,'kaikki')", (child, parent, kind, status, msc != msp))

    # staging para forms (necesita ON CONFLICT DO NOTHING); senses/etimología van directo por COPY.
    # SIN 'ON COMMIT DROP': commiteamos por archivo y la tabla debe sobrevivir entre commits.
    cur.execute("CREATE TEMP TABLE IF NOT EXISTS _f(id TEXT, lect_id TEXT, ipa_raw TEXT, orthography TEXT, etymology_text TEXT)")
    total_forms = total_sense = total_ety = 0
    for langname in args.languages:
        code = NAME2CODE.get(langname, langname.lower())
        ensure_lect(code)
        path = os.path.join(KDIR, f"{langname}.jsonl")
        if not os.path.isfile(path):
            print(f"!! no existe {path}"); continue
        form_buf, sense_buf, ety_buf = [], [], []
        n = 0
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            ety = d.get("ety"); ety_t = d.get("ety_t")
            if not (ety or ety_t) and not args.all:   # normal: solo con etimología; --all: toda entrada (ancestros)
                continue
            word = d.get("word"); pos = d.get("pos") or "x"
            fid = f"kaikki:{code}:{word}:{pos}"
            ipa = (d.get("ipa") or [None])[0]
            form_buf.append((fid, code, ipa, word, ety))
            for g in (d.get("gloss") or []):
                sense_buf.append((fid, g))
            # etimología estructurada: cadena de plantillas → aristas de lengua (inline) + de palabra (buffer)
            for t in (ety_t or []):
                nn = t.get("n"); a = t.get("a") or {}
                kind = KIND.get(nn)
                if not kind:
                    continue            # cog/suffix/prefix/… no son aristas de linaje aquí
                child_code = a.get("1"); parent_code = a.get("2"); parent_form = a.get("3")
                if not (child_code and parent_code):
                    continue
                # plantillas 'der'/'cog' con LISTA de lenguas ('es,pt','nap,scn') → no es un padre único:
                # saltar para no crear lects/aristas basura con coma o espacio.
                if any(bad in parent_code for bad in (",", " ")) or "," in child_code:
                    continue
                ensure_lect(child_code); ensure_lect(parent_code)     # cur.execute inline (sin COPY abierto)
                edge(child_code, parent_code, kind)
                ety_buf.append((fid, parent_form, parent_code, kind, a.get("5") or a.get("t")))
            n += 1
            if args.limit and n >= args.limit:
                break
        # --- flush del archivo vía COPY (forms por staging + ON CONFLICT; senses/etimología directo) ---
        cur.execute("TRUNCATE _f")
        with cur.copy("COPY _f(id,lect_id,ipa_raw,orthography,etymology_text) FROM STDIN") as cp:
            for r in form_buf:
                cp.write_row(r)
        cur.execute("INSERT INTO form(id,lect_id,ipa_raw,orthography,etymology_text,source_id) "
                    "SELECT DISTINCT ON (id) id,lect_id,ipa_raw,orthography,etymology_text,'kaikki' FROM _f "
                    "ON CONFLICT(id) DO NOTHING")
        with cur.copy("COPY sense(form_id,gloss) FROM STDIN") as cp:
            for r in sense_buf:
                cp.write_row(r)
        with cur.copy("COPY form_etymology(child_form_id,parent_form,parent_lect,kind,gloss,source_id) FROM STDIN") as cp:
            for fid, pform, pcode, knd, gl in ety_buf:
                cp.write_row((fid, pform, pcode, knd, gl, "kaikki"))
        total_forms += len(form_buf); total_sense += len(sense_buf); total_ety += len(ety_buf)
        conn.commit()
        print(f"· {langname}: {n} palabras con etimología")
    conn.commit()
    print(f"OK · formas={total_forms} · sentidos={total_sense} · aristas-palabra={total_ety} · "
          f"lects={len(lect_seen)} · aristas-lengua={len(edge_seen)}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
