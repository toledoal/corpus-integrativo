#!/usr/bin/env python3
"""Marcas de CALIDAD — no destructivas (el corpus crece, nada se tira; se ANOTA para consultar informado).

- form.is_proper   : heurística de nombre propio (inicial mayúscula). No se filtra; se marca.
- skeleton.core_valid : el core_skeleton debe ser SUBSECUENCIA del cons_skeleton (los consonantes de la raíz están,
                        en orden, dentro de los de la palabra). Si no → la descomposición es sospechosa → se marca
                        (pero se conserva el core).

Uso: .venv/bin/python ingest/mark_quality.py
"""
import psycopg

from config import DSN


def is_subseq(core, word):
    """¿la secuencia de consonantes del core es subsecuencia (en orden) de la de la palabra?"""
    c = core.split("·"); w = word.split("·")
    i = 0
    for x in w:
        if i < len(c) and c[i] == x:
            i += 1
    return i == len(c)


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("ALTER TABLE form ADD COLUMN IF NOT EXISTS is_proper BOOLEAN")
    cur.execute("ALTER TABLE skeleton ADD COLUMN IF NOT EXISTS core_valid BOOLEAN")
    conn.commit()

    # is_proper: inicial mayúscula (heurística, no filtro)
    cur.execute("UPDATE form SET is_proper = (orthography ~ '^[[:upper:]]') WHERE orthography IS NOT NULL")
    conn.commit()
    cur.execute("SELECT count(*) FROM form WHERE is_proper"); nprop = cur.fetchone()[0]

    # core_valid: subsecuencia
    cur.execute("SELECT id, cons_skeleton, core_skeleton FROM skeleton WHERE core_skeleton IS NOT NULL")
    rows = cur.fetchall(); nvalid = ninval = 0
    for sid, cons, core in rows:
        ok = bool(cons) and is_subseq(core, cons)
        cur.execute("UPDATE skeleton SET core_valid=%s WHERE id=%s", (ok, sid))
        if ok:
            nvalid += 1
        else:
            ninval += 1
    conn.commit()
    print(f"OK · is_proper marcados={nprop:,}  ·  core_valid=✔{nvalid:,} / �’sospechoso'{ninval:,} "
          f"({100*ninval/max(1,nvalid+ninval):.1f}% marcado sospechoso, CONSERVADO)")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
