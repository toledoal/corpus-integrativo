#!/usr/bin/env python3
"""Puebla la tabla `segment` (una fila por segmento IPA) desde form.segments_raw para TODA forma que aún no la tenga.

Capa pesada: ~6 filas por forma. Lexibank/IDS/NEL cargaron segments_raw como array pero NO poblaron `segment`
(a diferencia de kaikki vía segment_kaikki). Aquí se explota el array → segment(form_id, pos, ipa) vía COPY.
Incremental: solo formas sin filas en segment. Por lotes para no cargar todo en memoria.

Uso: .venv/bin/python ingest/build_segments_global.py
"""
import psycopg
from config import DSN

BATCH = 200_000


def main():
    rconn = psycopg.connect(DSN)                                    # conexión de LECTURA (cursor con nombre)
    wconn = psycopg.connect(DSN)                                    # conexión de ESCRITURA (commits independientes)
    cur = rconn.cursor(name="seg_cur"); cur.itersize = BATCH
    cur.execute("""SELECT f.id, f.segments_raw FROM form f
                   WHERE f.segments_raw IS NOT NULL
                     AND NOT EXISTS (SELECT 1 FROM segment s WHERE s.form_id=f.id)""")
    w = wconn.cursor()
    total = 0; buf = []
    for fid, segs in cur:
        for i, s in enumerate(segs or []):
            if s and s not in ("+", "_"):                 # salta marcadores de frontera
                buf.append((fid, i, s))
        if len(buf) >= 500_000:
            with w.copy("COPY segment(form_id,pos,ipa) FROM STDIN") as cp:
                for r in buf:
                    cp.write_row(r)
            wconn.commit(); total += len(buf); buf = []
            print(f"  … {total:,} segmentos", flush=True)
    if buf:
        with w.copy("COPY segment(form_id,pos,ipa) FROM STDIN") as cp:
            for r in buf:
                cp.write_row(r)
        wconn.commit(); total += len(buf)
    print(f"OK · segmentos nuevos = {total:,}")
    cur.close(); w.close(); rconn.close(); wconn.close()


if __name__ == "__main__":
    main()
