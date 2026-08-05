#!/usr/bin/env python3
"""Capa FEATURE — matriz de rasgos fonológicos (panphon F₂ⁿ) por fonema que aparece en el corpus romance.

Toma los fonemas DISTINTOS de la tabla `segment` (formas romance), pide a panphon su vector de rasgos
articulatorios (syl, son, cons, cont, nas, voi, lab, cor, dor, …) con valores {+1,0,−1} y los guarda en
`feature(phoneme, feat, value)`. Los segmentos que panphon no reconoce se OMITEN (se podrán marcar aparte).
La tabla es de definición fonética (no atada a una familia); la poblamos con los fonemas que Romance usa.

Uso: .venv/bin/python ingest/build_features.py
"""
import psycopg
import panphon
from families import active

from config import DSN
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]


def main():
    ft = panphon.FeatureTable()
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} ({len(MEMBERS)} lects)")
    # borrado ACOTADO: solo los fonemas que aparecen en esta familia (preserva fonemas únicos de otras)
    cur.execute("""DELETE FROM feature WHERE phoneme IN (
                     SELECT DISTINCT s.ipa FROM segment s JOIN form f ON f.id=s.form_id
                     WHERE f.lect_id = ANY(%s) AND s.ipa IS NOT NULL)""", (MEMBERS,))
    conn.commit()

    cur.execute("""SELECT DISTINCT s.ipa FROM segment s JOIN form f ON f.id=s.form_id
                   WHERE f.lect_id = ANY(%s) AND s.ipa IS NOT NULL""", (MEMBERS,))
    phonemes = [r[0] for r in cur.fetchall()]
    print(f"fonemas distintos en Romance: {len(phonemes):,}")

    nph = nrow = nmiss = 0
    for ph in phonemes:
        segs = ft.word_fts(ph)                    # lista de Segment (panphon re-segmenta)
        if not segs:
            nmiss += 1; continue
        fts = segs[0]                             # primer segmento base
        for feat, val in fts.items():             # panphon ya entrega enteros: +1 / 0 / -1
            cur.execute("INSERT INTO feature(phoneme,feat,value) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                        (ph, feat, int(val)))
            nrow += 1
        nph += 1
        if nph % 200 == 0: conn.commit()
    conn.commit()
    print(f"OK · fonemas con rasgos={nph:,} · filas={nrow:,} · sin-reconocer(omitidos)={nmiss:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
