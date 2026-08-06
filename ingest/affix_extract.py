#!/usr/bin/env python3
"""Extrae el INVENTARIO DE AFIJOS desde Kaikki → tabla `affix` (paso 1 del core_skeleton morfológico).

Kaikki lista los afijos como entradas propias (pos ∈ {suffix, prefix, affix, interfix, circumfix}). Los cargamos
como entradas-morfema de primera clase con: forma, tipo, función (gloss), origen (etimología), y su ESQUELETO
consonántico propio (letras + código de clase) — calculado desde la ortografía (Latín/Romance ≈ fonémico para
consonantes). Es la base para pelar afijos y derivar el core_skeleton de las palabras.

Uso: .venv/bin/python ingest/affix_extract.py Latin Spanish
"""
import argparse, json, os, unicodedata
import psycopg

from config import DSN
from config import KDIR
from families import all_kaikki_files
NAME2CODE = all_kaikki_files()   # unión de TODAS las familias definidas
AFFIX_POS = {"suffix": "suffix", "prefix": "prefix", "affix": "suffix", "interfix": "infix",
             "circumfix": "prefix", "infix": "infix"}
SYM = dict(zip("PTKSLMN", "ΦΘΧΣΛϺΞ"))
# letra ortográfica Latín/Romance → clase OAS (aprox. para el esqueleto del afijo)
LET2CLASS = {}
for chars, cl in [("pbfv", "P"), ("tdθ", "T"), ("ckgqx", "K"), ("szçñ".replace("ñ", ""), "S"),
                  ("lr", "L"), ("m", "M"), ("n", "N")]:
    for ch in chars:
        LET2CLASS[ch] = cl
LET2CANON = {"c": "k", "q": "k", "v": "b", "f": "f", "x": "x", "z": "s"}


def clean(w):
    return "".join(c for c in unicodedata.normalize("NFD", w.strip("-–—· "))
                   if unicodedata.category(c) != "Mn").lower()


def affix_skeleton(form):
    cons, syms = [], []
    for ch in clean(form):
        cl = LET2CLASS.get(ch)
        if cl:
            cons.append(LET2CANON.get(ch, ch)); syms.append(SYM[cl])
    return ("·".join(cons) or None, "·".join(syms) or None)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("languages", nargs="+"); args = ap.parse_args()
    conn = psycopg.connect(DSN, autocommit=False); cur = conn.cursor()
    # borrado ACOTADO a las lenguas que se (re)cargan (no wipea afijos de otras familias)
    codes = sorted({NAME2CODE.get(l, l.lower()) for l in args.languages})
    cur.execute("DELETE FROM affix WHERE source_id='kaikki' AND origin_lect = ANY(%s)", (codes,))
    conn.commit()
    n = 0
    for langname in args.languages:
        code = NAME2CODE.get(langname, langname.lower())
        path = os.path.join(KDIR, f"{langname}.jsonl")
        if not os.path.isfile(path):
            continue
        # garantiza el lect (FK de affix.origin_lect); si kaikki_ingest ya lo creó, no lo pisa
        cur.execute("INSERT INTO lect(id,name,level,attested,source_id) VALUES(%s,%s,'lengua',true,'kaikki') "
                    "ON CONFLICT(id) DO NOTHING", (code, langname.replace("_", " ")))
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            pos = d.get("pos")
            if pos not in AFFIX_POS:
                continue
            form = d.get("word")
            cons, symcode = affix_skeleton(form)
            func = (d.get("gloss") or [None])[0]
            gram = (d.get("ety") or "")[:200] or None
            aid = f"afx:{code}:{form}"
            cur.execute(
                "INSERT INTO affix(id,form,type,function_gloss,grammaticalization,cons_skeleton,code,origin_lect,source_id) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'kaikki') ON CONFLICT(id) DO NOTHING",
                (aid, form, AFFIX_POS[pos], func, gram, cons, symcode, code))
            n += 1
        conn.commit()
        print(f"· {langname}: afijos acumulados {n}")
    print(f"OK · afijos extraídos={n}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
