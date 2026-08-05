#!/usr/bin/env python3
"""Capa PROTOFORM_HYPOTHESIS — la proto-forma de cada cognate_set = su ETYMON (del id del set).

Honestidad epistémica: si el etymon es LATÍN (atestiguado), status='atestiguado', probability=1.0; si es un
PROTO reconstruido (itc-pro/ine-pro), status='reconstruido', probability=0.5. No inventamos reconstrucción donde
hay latín documentado — solo copiamos el ancestro que ya trae el grafo. Modelo='kaikki-etymon'.

Uso: .venv/bin/python ingest/build_protoforms.py
"""
import psycopg
from families import active

DSN = "host=/tmp/ci_pg port=5433 user=postgres dbname=corpus_integrativo"
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]
# clave-canónica de cada nivel de ancestro → (status, prob). Latín=atestiguado(1.0); proto=reconstruido(0.5).
STATUS_BY_KEY = {lects[0]: (st, 1.0 if st == "atestiguado" else 0.5) for _lbl, lects, st in FAM["ancestors"]}


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} · claves de ancestro: {STATUS_BY_KEY}")
    # sets de ESTA familia (con al menos un miembro de la familia) + la VARIEDAD concreta del etymon
    cur.execute("""SELECT DISTINCT cs.id, cs.ancestor_lect FROM cognate_set cs
                   JOIN cognate_member cm ON cm.cognate_set_id=cs.id JOIN form f ON f.id=cm.form_id
                   WHERE f.lect_id = ANY(%s)""", (MEMBERS,))
    sets = cur.fetchall()
    setids = [r[0] for r in sets]
    cur.execute("DELETE FROM protoform_hypothesis WHERE cognate_set_id = ANY(%s)", (setids,)); conn.commit()

    nph = 0
    for setid, anc in sets:                            # id = 'cog:<clave>:<forma>'; anc = variedad concreta
        try:
            _, key, form = setid.split(":", 2)
        except ValueError:
            continue
        status, prob = STATUS_BY_KEY.get(key, ("atestiguado", 1.0))   # ancestro atestiguado por defecto
        plect = anc or key                             # variedad concreta (la-vul/la-cla…) si se registró
        cur.execute("""INSERT INTO protoform_hypothesis(cognate_set_id,lect_id,form,model,probability,status)
                       VALUES(%s,%s,%s,'kaikki-etymon',%s,%s)""", (setid, plect, form, prob, status))
        nph += 1
        if nph % 5000 == 0: conn.commit()
    conn.commit()
    print(f"OK · proto-formas hipotetizadas={nph:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
