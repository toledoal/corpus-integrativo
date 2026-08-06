#!/usr/bin/env python3
"""Recomputa el ESQUELETO CONSONÁNTICO (objeto endolingüístico) desde los segmentos ingeridos → tablas
`skeleton` + `skeleton_lineage`.  LIMPIO desde el núcleo: no ingiere el web/data viejo; porta el mapeo canónico OAS
(idéntico a src/build_skeltree.py) y lo aplica a los `segments_raw` de cada forma.

- cons_skeleton (LETRAS): secuencia COMPLETA de consonantes canónicas por valor cuálico (róticas→r, dorsales→x/h…).
- code (SÍMBOLOS de clase): Φ Θ Χ Σ Λ Ϻ Ξ, la secuencia de clases.
- core_skeleton: NULL por ahora (requiere morfología → tras el loader Kaikki).
- skeleton_lineage: agrupa un mismo `code` a través de estadios/ramas (resonancia estructural).

Uso: .venv/bin/python ingest/recompute_skeleton.py [--only-new]
     --only-new: solo formas SIN esqueleto (incremental, para al agregar una familia sin reprocesar todo).
"""
import argparse
import unicodedata
import psycopg

from config import DSN

SYM = dict(zip("PTKSLMN", "ΦΘΧΣΛϺΞ"))
IPA = {}
for chars, cl in [("pbɓʙɸβfvʋwⱱʍ", "P"), ("tdʈɖθðɗþ", "T"), ("szʃʒʂʐɕʑʦʣʧʤʨʥſß", "S"),
                  ("lɫɭʎʟrɾɹɻʀʁłɽɬɮǁɺ", "L"), ("kgɡcɟxɣχqɢʔhɦħʕçʝɠʄɧ", "K"), ("mɱ", "M"), ("nɳɲŋɴ", "N")]:
    for ch in chars:
        IPA[ch] = cl
# vocales: IPA + redondeadas germánicas (ʏ ɶ ɞ ᵻ ᵿ) + yers/nasales eslavas de reconstrucción (ъ ь ǫ ę ě ą)
VOW = set("aeiouyæœøɑɒɐɘɵɛɔəɜɤʌɨʉʊɪɚɝʏɶɞᵻᵿъьǫęěąųẽɯ"); GLI = set("jɥɰ")   # +ɯ (posterior no-red., céltico)
# marcas de tono/prosodia que NO son segmento (tono superíndice ±, flechas de entonación, dobles barras) → se ignoran
IGNORE = set("¹²³⁴⁵⁶⁷⁸⁹⁰⁻⁺⁽⁾↗↘↑↓⫽ǀǃ:◌0123456789*ꝛ⁊&")   # tono/entonación + paréntesis palatalización eslava + ◌ (ancla devanagari)
SKEL_NORM = {}
for _chars, _canon in [("lɫɭʟłɬɮǁ", "l"), ("ʎ", "ʎ"), ("rɾɹɻʀʁɺ", "r"),
                       ("k", "k"), ("gɡ", "g"), ("cɟ", "c"), ("q", "q"),
                       ("xɣχçʝɧ", "x"), ("hɦʔħʕ", "h"),
                       ("nɳ", "n"), ("ŋɲɴ", "n"), ("mɱ", "m"),      # nasales → canónica n/m (fix batería A)
                       ("rɾɹɻʀʁɽ", "r"), ("dɗ", "d")]:              # róticas retroflejas / implosivas → canónica
    for _ch in _chars:
        SKEL_NORM[_ch] = _canon
BOUNDARY = set("+-_~,;")                                            # compuesto/multi-palabra (+/-/_) + variante (~)

# ── Regla BICLASE (doc oas-segmentos-biclase, revisión versionada del mapeo IPA→clase) ──
# Segmentos IPA únicos que comprometen DOS regiones a la vez → aportan DOS clases al esqueleto.
# Orden: base·Χ (por defecto, §9). El IPA original se conserva en form.segments_raw (trazabilidad C0★★).
BICLASS = {}
for _chs, _pair in [("ʃʒʂʐɕʑ", (("S", "s"), ("K", "x"))),         # sibilantes desplazadas → Σ·Χ
                    ("ɳɲŋɴ",   (("N", "n"), ("K", "x"))),         # nasales dorsales       → Ξ·Χ
                    ("ʎ",       (("L", "l"), ("K", "x")))]:        # lateral palatal        → Λ·Χ
    for _c in _chs:
        BICLASS[_c] = _pair
# Africadas: NO biclase — transición Θ→Σ, se leen por su DESTINO (Σ). Símbolo único o t/d + sibilante.
AFF_SINGLE = set("ʦʣʧʤʨʥ")


def _is_affricate(base):
    if any(c in AFF_SINGLE for c in base):
        return True
    return len(base) >= 2 and base[0] in "td" and base[-1] in "szʃʒʂʐɕʑ"


def consonant_classes(base, biclass=False):
    """→ lista de (clase, canónica) de un segmento: 2 pares si es BICLASE (y biclass=True), 1 si simple/africada.
    DEFAULT biclass=False: la biclase a ciegas REDUJO la conservación de código en todas las familias (medido,
    ver analysis/biclass_conservation.py) → se deja apagada; sigue disponible para investigarla condicionada a
    genealogía. La africada tʃ→Σ (por destino) sí queda siempre (corrige el bug del tie-bar previo)."""
    if _is_affricate(base):                                       # africada primero (tʃ contiene ʃ pero es Σ)
        return [("S", "s")]
    for ch in base:
        if ch in BICLASS:
            return list(BICLASS[ch]) if biclass else [BICLASS[ch][0]]   # dos clases, o solo la base
    for ch in base:                                               # clase simple: 1er char clasificable
        if ch in VOW or ch in GLI:
            return []
        if ch in IPA:
            return [(IPA[ch], base)]
    return []


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


def compute(segments, biclass=False):
    """Devuelve (cons, code, vowels, cv, is_compound). Vocales CONSERVADAS; compuestos marcados.
    biclass=False por DEFAULT (revertido: reducía la conservación de código, medido por familia).
    BICLASE con GUARDA DE ASIMILACIÓN: un dorsal-nasal/sibilante cuya coloración Χ es adyacente a un
    consonante Χ siguiente (ŋ+g en 'banco'/'angustus') es asimilación, NO ŋ fonémica → se lee solo la base
    (no se duplica la Χ; el dorso lo aporta el segmento velar siguiente). La ŋ que absorbió el velar (sin
    velar siguiente: 'sing') sí es biclase Ξ·Χ."""
    # 1) clasificar cada segmento en una celda
    cells = []
    for seg in segments:
        base = _clean(seg)
        if not base or set(base) <= BOUNDARY:
            cells.append(("+",)); continue
        pairs = consonant_classes(base, biclass)
        if pairs:
            cells.append(("C", pairs))
        elif any(ch in GLI for ch in base):
            cells.append(("G",))
        elif any(ch in VOW for ch in base):
            cells.append(("V", seg))
        elif set(base) <= IGNORE:
            cells.append(("T",))
        else:
            cells.append(("?",))
    # 2) guarda de asimilación: biclase (base·Χ) + siguiente consonante Χ → colapsar a base
    for i, c in enumerate(cells):
        if c[0] == "C" and len(c[1]) == 2 and c[1][1][0] == "K":
            nxt = next((cells[j] for j in range(i + 1, len(cells)) if cells[j][0] in ("C", "V")), None)
            if nxt and nxt[0] == "C" and nxt[1][0][0] == "K":
                cells[i] = ("C", [c[1][0]])            # solo la base; el dorso es el velar siguiente
    # 3) ensamblar
    cons, syms, vows, cv = [], [], [], []
    compound = False
    for c in cells:
        if c[0] == "+":
            compound = True; cv.append("+")
        elif c[0] == "C":
            for cls, canon in c[1]:
                cons.append(norm_char(canon)); syms.append(SYM[cls])
            cv.append("C")
        elif c[0] == "G":
            cv.append("G")
        elif c[0] == "V":
            vows.append(c[1]); cv.append("V")
        elif c[0] == "T":
            cv.append("T")
        else:
            cv.append("?")
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
    ap = argparse.ArgumentParser(); ap.add_argument("--only-new", action="store_true"); a = ap.parse_args()
    where = "segments_raw IS NOT NULL"
    if a.only_new:   # incremental: solo formas que aún NO tienen esqueleto
        where += " AND NOT EXISTS (SELECT 1 FROM skeleton sk WHERE sk.form_id=form.id)"
    cur.execute(f"SELECT id, lect_id, segments_raw FROM form WHERE {where}")
    rows = cur.fetchall()
    lineage_cache = {}
    # 1) computar esqueletos + upsert de linajes (códigos únicos, pocos miles)
    computed = []
    for fid, lect, segs in rows:
        cons, code, vowels, cv, compound = compute(segs or [])
        if not cons and not vowels:
            continue
        if code and code not in lineage_cache:
            cur.execute("INSERT INTO skeleton_lineage(code) VALUES(%s) ON CONFLICT(code) DO UPDATE SET code=EXCLUDED.code RETURNING id", (code,))
            lineage_cache[code] = cur.fetchone()[0]
        computed.append((f"SK:{fid}", fid, lect, cons, code,
                         lineage_cache.get(code) if code else None, vowels, cv, compound))
    # 2) COPY a temp + UPSERT masivo (una sola sentencia; preserva core_skeleton existente)
    cur.execute("""CREATE TEMP TABLE _sk(id TEXT, form_id TEXT, stage_lect_id TEXT, cons_skeleton TEXT, code TEXT,
                   skeleton_lineage_id INT, vowels TEXT, cv_template TEXT, is_compound BOOLEAN) ON COMMIT DROP""")
    with cur.copy("COPY _sk(id,form_id,stage_lect_id,cons_skeleton,code,skeleton_lineage_id,vowels,cv_template,is_compound) FROM STDIN") as cp:
        for r in computed:
            cp.write_row(r)
    cur.execute("""INSERT INTO skeleton(id,form_id,stage_lect_id,cons_skeleton,code,skeleton_lineage_id,vowels,cv_template,is_compound)
                   SELECT id,form_id,stage_lect_id,cons_skeleton,code,skeleton_lineage_id,vowels,cv_template,is_compound FROM _sk
                   ON CONFLICT(id) DO UPDATE SET cons_skeleton=EXCLUDED.cons_skeleton,code=EXCLUDED.code,
                     skeleton_lineage_id=EXCLUDED.skeleton_lineage_id,vowels=EXCLUDED.vowels,
                     cv_template=EXCLUDED.cv_template,is_compound=EXCLUDED.is_compound""")
    conn.commit()
    print(f"OK · esqueletos={len(computed):,} · linajes(códigos únicos)={len(lineage_cache):,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
