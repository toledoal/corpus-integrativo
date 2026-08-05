#!/usr/bin/env python3
"""Capa de CONTACTO — substrate_edge (préstamos hacia Romance) + contact_cohort (cohortes por lengua-fuente).

De `form_etymology` con kind='prestamo' y forma-hija ROMANCE: cada arista → substrate_edge(form_id, source_lect,
status='atestiguado', probability=1.0) — Kaikki afirma el préstamo. Luego agrupamos los préstamos en COHORTES por
(lect-hija ← lengua-fuente): p. ej. 'es←ar' = arabismos del español, 'fr←frk' = francismos, etc. Cada cohorte
(contact_cohort) reúne sus formas (cohort_member). Las lenguas FUENTE pueden ser no-romance (árabe, fráncico): son
el origen de un préstamo ENTRANTE, no añaden lects romances germánicos/eslavos (el guardarraíl sigue intacto).

Uso: .venv/bin/python ingest/build_contact.py
"""
import psycopg
from collections import defaultdict
from families import active

DSN = "host=/tmp/ci_pg port=5433 user=postgres dbname=corpus_integrativo"
FAM_NAME, FAM = active()
MEMBERS = FAM["members"]


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print(f"familia activa: {FAM_NAME} ({len(MEMBERS)} lects)")
    # borrado ACOTADO a la familia: préstamos cuyas HIJAS son de esta familia
    fam_forms = "(SELECT id FROM form WHERE lect_id = ANY(%s))"
    cur.execute(f"DELETE FROM cohort_member WHERE form_id IN {fam_forms}", (MEMBERS,))
    cur.execute(f"DELETE FROM substrate_edge WHERE form_id IN {fam_forms}", (MEMBERS,))
    cur.execute("DELETE FROM contact_cohort cc WHERE NOT EXISTS (SELECT 1 FROM cohort_member m WHERE m.cohort_id=cc.id)")
    conn.commit()

    # préstamos hacia formas de la familia (una arista 'prestamo' por hija; toma la primera fuente por forma)
    cur.execute("""SELECT DISTINCT ON (fe.child_form_id) fe.child_form_id, fe.parent_lect, f.lect_id
                   FROM form_etymology fe JOIN form f ON f.id=fe.child_form_id
                   WHERE fe.kind='prestamo' AND f.lect_id = ANY(%s) AND fe.parent_lect IS NOT NULL
                   ORDER BY fe.child_form_id, fe.id""", (MEMBERS,))
    edges = cur.fetchall()
    nsub = 0
    cohorts = defaultdict(list)                  # (child_lect, source_lect) -> [form_id]
    for form_id, source_lect, child_lect in edges:
        cur.execute("""INSERT INTO substrate_edge(form_id,source_lect,probability,status)
                       VALUES(%s,%s,1.0,'atestiguado')""", (form_id, source_lect))
        cohorts[(child_lect, source_lect)].append(form_id)
        nsub += 1
        if nsub % 20000 == 0: conn.commit()
    conn.commit()

    ncoh = nmem = 0
    for (child_lect, source_lect), fids in cohorts.items():
        if len(fids) < 3:                        # cohorte = ≥3 préstamos del mismo origen (patrón, no anécdota)
            continue
        cid = f"contact:{child_lect}<{source_lect}"
        cur.execute("""INSERT INTO contact_cohort(id,pattern,note) VALUES(%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
                    (cid, f"{child_lect}←{source_lect}", f"{len(fids)} préstamos {source_lect}→{child_lect}"))
        ncoh += 1
        for fid in fids:
            cur.execute("INSERT INTO cohort_member(cohort_id,form_id) VALUES(%s,%s)", (cid, fid))
            nmem += 1
        if ncoh % 500 == 0: conn.commit()
    conn.commit()
    print(f"OK · substrate_edge={nsub:,} · cohortes={ncoh:,} · miembros={nmem:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
