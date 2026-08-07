#!/usr/bin/env python3
"""Capa CRIPTOLÓGICA global — firma `crypto` (self_info) por forma, para TODA forma con esqueleto y sin crypto.

self_info = −Σ log2 p(clase) sobre la distribución unigrama GLOBAL de clases del código (autoinformación del
esqueleto = "peso" del mensaje bajo el cifrado, §6a). Idéntico a build_correspondences pero NO family-scoped:
cubre Lexibank/IDS/NEL (fuera de familias IE). feature_vectors = {"classes":[…]} JSONB.

Incremental: solo formas con skeleton.code y sin fila crypto. Uso: .venv/bin/python ingest/build_crypto_global.py
"""
import json
import math
import psycopg
from config import DSN


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    # unigrama GLOBAL de clases (símbolos del código, separados por ·)
    cur.execute("""SELECT cls, count(*) FROM (
                     SELECT unnest(string_to_array(code,'·')) cls FROM skeleton
                     WHERE code IS NOT NULL AND code<>'') t GROUP BY 1""")
    unigram = {c: n for c, n in cur.fetchall()}
    total = sum(unigram.values())
    logp = {c: -math.log2(n / total) for c, n in unigram.items()}
    print(f"unigrama de clases: {len(unigram)} clases · {total:,} ocurrencias")

    # formas con esqueleto y SIN crypto (streaming por dos conexiones)
    rconn = psycopg.connect(DSN); wconn = psycopg.connect(DSN)
    rc = rconn.cursor(name="cry"); rc.itersize = 200_000
    rc.execute("""SELECT sk.form_id, sk.id, sk.code FROM skeleton sk
                  WHERE sk.code IS NOT NULL AND sk.code<>''
                    AND NOT EXISTS (SELECT 1 FROM crypto c WHERE c.form_id=sk.form_id)""")
    w = wconn.cursor()
    n = 0; buf = []
    for fid, sid, code in rc:
        classes = code.split("·")
        si = sum(logp.get(c, 0.0) for c in classes)
        buf.append((fid, sid, json.dumps({"classes": classes}), round(si, 4)))
        if len(buf) >= 500_000:
            with w.copy("COPY crypto(form_id,skeleton_id,feature_vectors,self_info) FROM STDIN") as cp:
                for r in buf:
                    cp.write_row(r)
            wconn.commit(); n += len(buf); buf = []
            print(f"  … {n:,} crypto", flush=True)
    if buf:
        with w.copy("COPY crypto(form_id,skeleton_id,feature_vectors,self_info) FROM STDIN") as cp:
            for r in buf:
                cp.write_row(r)
        wconn.commit(); n += len(buf)
    print(f"OK · crypto nuevos = {n:,}")
    rc.close(); w.close(); rconn.close(); wconn.close(); cur.close(); conn.close()


if __name__ == "__main__":
    main()
