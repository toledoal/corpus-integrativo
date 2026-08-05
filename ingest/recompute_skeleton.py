#!/usr/bin/env python3
"""Recomputa el ESQUELETO CONSONÁNTICO (objeto endolingüístico) desde los segmentos ingeridos → tablas
`skeleton` + `skeleton_lineage`.  LIMPIO desde el núcleo: no ingiere el web/data viejo; porta el mapeo canónico OAS
(idéntico a src/build_skeltree.py) y lo aplica a los `segments_raw` de cada forma.

- cons_skeleton (LETRAS): secuencia COMPLETA de consonantes canónicas por valor cuálico (róticas→r, dorsales→x/h…).
- code (SÍMBOLOS de clase): Φ Θ Χ Σ Λ Ϻ Ξ, la secuencia de clases.
- core_skeleton: NULL por ahora (requiere morfología → tras el loader Kaikki).
- skeleton_lineage: agrupa un mismo `code` a través de estadios/ramas (resonancia estructural).

Uso: .venv/bin/python ingest/recompute_skeleton.py
"""
import unicodedata
import psycopg

DSN = "host=/tmp/ci_pg port=5433 user=postgres dbname=corpus_integrativo"

SYM = dict(zip("PTKSLMN", "ΦΘΧΣΛϺΞ"))
IPA = {}
for chars, cl in [("pbɓʙɸβfvʋwⱱ", "P"), ("tdʈɖθðɗ", "T"), ("szʃʒʂʐɕʑʦʣʧʤʨʥ", "S"),
                  ("lɫɭʎʟrɾɹɻʀʁłɽ", "L"), ("kgɡcɟxɣχqɢʔhɦħʕçʝɠʄ", "K"), ("mɱ", "M"), ("nɳɲŋɴ", "N")]:
    for ch in chars:
        IPA[ch] = cl
VOW = set("aeiouyæœøɑɒɐɘɵɛɔəɜɤʌɨʉʊɪɚɝ"); GLI = set("jɥ")
SKEL_NORM = {}
for _chars, _canon in [("lɫɭʟł", "l"), ("ʎ", "ʎ"), ("rɾɹɻʀʁ", "r"),
                       ("k", "k"), ("gɡ", "g"), ("cɟ", "c"), ("q", "q"),
                       ("xɣχçʝ", "x"), ("hɦʔħʕ", "h"),
                       ("nɳ", "n"), ("ŋɲɴ", "n"), ("mɱ", "m"),      # nasales → canónica n/m (fix batería A)
                       ("rɾɹɻʀʁɽ", "r"), ("dɗ", "d")]:              # róticas retroflejas / implosivas → canónica
    for _ch in _chars:
        SKEL_NORM[_ch] = _canon
BOUNDARY = set("+-_~")                                            # compuesto/multi-palabra (+/-/_) + variante (~)


def seg_class_char(seg):
    s = "".join(c for c in unicodedata.normalize("NFD", seg)
                if unicodedata.category(c) not in ("Mn", "Lm", "Sk", "Cf")).replace("͡", "").replace("͜", "")
    for ch in s.lower():
        if ch in VOW or ch in GLI:
            return None
        if ch in IPA:
            return (IPA[ch], s.lower())
    return None


def norm_char(ch):
    if ch in SKEL_NORM:
        return SKEL_NORM[ch]
    for c in ch:
        if c in SKEL_NORM:
            return SKEL_NORM[c]
    return ch


def _clean(seg):
    return "".join(c for c in unicodedata.normalize("NFD", seg)
                   if unicodedata.category(c) not in ("Mn", "Lm", "Sk", "Cf")).replace("͡", "").replace("͜", "").lower()


def compute(segments):
    """Devuelve (cons, code, vowels, cv, is_compound). Vocales CONSERVADAS; compuestos marcados."""
    cons, syms, vows, cv = [], [], [], []
    compound = False
    for seg in segments:
        base = _clean(seg)
        if not base or set(base) <= BOUNDARY:        # marcador de compuesto (+/_/-): frontera, no '?'
            compound = True; cv.append("+"); continue
        cc = seg_class_char(seg)
        if cc:
            cons.append(norm_char(cc[1])); syms.append(SYM[cc[0]]); cv.append("C")
        elif any(ch in GLI for ch in base):
            cv.append("G")                            # glide
        elif any(ch in VOW for ch in base):
            vows.append(seg); cv.append("V")          # VOCAL: IPA crudo (calidad/longitud/tono)
        else:
            cv.append("?")                            # residual real (tono suelto, símbolo raro)
    if not cons and not vows:
        return None, None, None, None, compound
    return ("·".join(cons) or None, "·".join(syms) or None, "·".join(vows) or None, "".join(cv), compound)


def main():
    conn = psycopg.connect(DSN, autocommit=False)
    cur = conn.cursor()
    cur.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_sklin_code') "
                "THEN ALTER TABLE skeleton_lineage ADD CONSTRAINT uq_sklin_code UNIQUE(code); END IF; END $$;")
    cur.execute("ALTER TABLE skeleton ADD COLUMN IF NOT EXISTS vowels TEXT, ADD COLUMN IF NOT EXISTS cv_template TEXT, "
                "ADD COLUMN IF NOT EXISTS is_compound BOOLEAN DEFAULT FALSE;")
    conn.commit()
    cur.execute("SELECT id, lect_id, segments_raw FROM form WHERE segments_raw IS NOT NULL")
    rows = cur.fetchall()
    lineage_cache = {}
    n = 0
    for fid, lect, segs in rows:
        cons, code, vowels, cv, compound = compute(segs or [])
        if not cons and not vowels:
            continue
        lin = None
        if code:
            if code not in lineage_cache:
                cur.execute("INSERT INTO skeleton_lineage(code) VALUES(%s) ON CONFLICT(code) DO UPDATE SET code=EXCLUDED.code RETURNING id", (code,))
                lineage_cache[code] = cur.fetchone()[0]
            lin = lineage_cache[code]
        cur.execute(
            "INSERT INTO skeleton(id,form_id,stage_lect_id,cons_skeleton,core_skeleton,code,skeleton_lineage_id,vowels,cv_template,is_compound) "
            "VALUES(%s,%s,%s,%s,NULL,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET "
            "cons_skeleton=EXCLUDED.cons_skeleton,code=EXCLUDED.code,skeleton_lineage_id=EXCLUDED.skeleton_lineage_id,"
            "vowels=EXCLUDED.vowels,cv_template=EXCLUDED.cv_template,is_compound=EXCLUDED.is_compound",
            (f"SK:{fid}", fid, lect, cons, code, lin, vowels, cv, compound))
        n += 1
        if n % 5000 == 0:
            conn.commit(); print(f"  … {n} esqueletos")
    conn.commit()
    print(f"OK · esqueletos={n} · linajes(códigos únicos)={len(lineage_cache)}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
