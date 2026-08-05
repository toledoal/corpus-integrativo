#!/usr/bin/env python3
"""Segmenta el IPA de las formas Kaikki → tabla `segment` + `form.segments_raw`  (desbloquea esqueleto de ~110k formas).

Kaikki da la CADENA IPA (ej. '/anɡosˈtuɾa/') pero no los segmentos. Aquí un segmentador que:
  - limpia delimitadores (/ [ ] ( ) espacios) y separa por sílaba (.),
  - une diacríticos/modificadores (longitud ː, palatalización ʲ, nasal ̃, tono, africadas con tie-bar) al segmento,
  - CONSERVA el ACENTO: la vocal tras ˈ/ˌ queda marcada tónica (empieza a llenar la capa de prosodia).
Luego correr `recompute_skeleton.py` para que estas formas obtengan esqueleto+vocales.

Uso: .venv/bin/python ingest/segment_kaikki.py
"""
import unicodedata
import psycopg

from config import DSN
STRIP = set("/[]()ˈˌ‿|ˑ '\"")          # ˈˌ se manejan aparte (marcan acento) — aquí solo por si quedan sueltos
TIE = {"͡", "͜"}               # ͡ ͜  (africadas: unen el siguiente base)


def is_modifier(ch):
    if unicodedata.combining(ch):        # diacríticos combinantes (nasal, tono, etc.)
        return True
    cat = unicodedata.category(ch)
    return cat in ("Lm", "Sk") or ch in "ːˑ˞ⁿˡʰʱ"   # letras/símbolos modificadores + longitud


def is_vowel(seg):
    for ch in seg:
        if ch in "aeiouyæœøɑɒɐɘɵɛɔəɜɤʌɨʉʊɪɚɝ":
            return True
    return False


def segment(ipa):
    """Devuelve lista de (seg, syllable, stressed)."""
    s = ipa.split("~")[0]                            # solo la PRIMERA variante de pronunciación (~ separa variantes)
    s = unicodedata.normalize("NFD", s.strip())      # descompone vocales precompuestas (ã→a+̃) → base + modificador
    if s and s[0] in "/[":
        s = s.strip("/[]")
    out = []; cur = ""; syl = 0; stress_next = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in ("ˈ", "ˌ"):
            stress_next = True; i += 1; continue
        if ch == ".":
            syl += 1; i += 1; continue
        if ch in STRIP:
            i += 1; continue
        if ch in TIE:                     # tie-bar: pega el siguiente base al segmento actual
            cur += ch
            if i + 1 < len(s):
                cur += s[i + 1]; i += 2
            else:
                i += 1
            continue
        if is_modifier(ch) and cur:       # modificador → se adhiere al segmento actual
            cur += ch; i += 1; continue
        # base nuevo → cierra el anterior
        if cur:
            v = is_vowel(cur)
            out.append((cur, syl, stress_next and v))
            if v:
                stress_next = False        # el acento lo consume la vocal (núcleo)
        cur = ch; i += 1
    if cur:
        v = is_vowel(cur)
        out.append((cur, syl, stress_next and v))
    return out


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("SELECT id, ipa_raw FROM form WHERE source_id='kaikki' AND ipa_raw IS NOT NULL AND segments_raw IS NULL")
    rows = cur.fetchall()
    print(f"formas Kaikki a segmentar: {len(rows):,}")
    n = nseg = 0
    for fid, ipa in rows:
        segs = segment(ipa)
        if not segs:
            continue
        cur.execute("UPDATE form SET segments_raw=%s WHERE id=%s", ([x[0] for x in segs], fid))
        for pos, (seg, syl, stressed) in enumerate(segs):
            cur.execute("INSERT INTO segment(form_id,pos,ipa,syllable,is_stressed) VALUES(%s,%s,%s,%s,%s)",
                        (fid, pos, seg, syl, stressed))
            nseg += 1
        n += 1
        if n % 5000 == 0:
            conn.commit(); print(f"  … {n:,} formas")
    conn.commit()
    print(f"OK · formas segmentadas={n:,} · segmentos={nseg:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
