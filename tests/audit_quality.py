#!/usr/bin/env python3
"""Audit de CALIDAD del corpus (distinto de tests/qa.py, que es integridad estructural).

Caza clases de bugs semánticos/genealógicos que la integridad no ve: mislabels herencia/préstamo, mapeos de
concepto erróneos, ciclos de linaje, procedencia rota, y avisa de datos en cuarentena de licencia. Cada chequeo
reporta un conteo y, si hay, una muestra. Umbral orientativo, no bloqueante (la calidad es un gradiente).

Uso: .venv/bin/python tests/audit_quality.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingest"))
import psycopg
from config import DSN

CHECKS = [
 ("LIN · herencia cruza familia (debería ser préstamo)",
  """SELECT count(*) FROM form_etymology fe JOIN form cf ON cf.id=fe.child_form_id
     JOIN lect lc ON lc.id=cf.lect_id JOIN lect lp ON lp.id=fe.parent_lect
     WHERE fe.kind='herencia' AND lc.family IS NOT NULL AND lp.family IS NOT NULL AND lc.family<>lp.family""",
  "la herencia NO cruza familias; si cruza es préstamo/contacto"),
 ("LIN · ciclos de 2 (a↔b)",
  """SELECT count(*) FROM form_etymology e1 JOIN form_etymology e2
     ON e1.parent_form_id=e2.child_form_id AND e2.parent_form_id=e1.child_form_id WHERE e1.parent_form_id IS NOT NULL""",
  "contradictorio; el walk es cycle-safe pero conviene minimizar"),
 ("SEM · concepto que no aparece en ningún sentido (kaikki)",
  """SELECT count(*) FROM form f WHERE f.source_id='kaikki' AND f.concept_id IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM sense s WHERE s.form_id=f.id
       AND lower(s.gloss) LIKE '%'||lower((SELECT gloss_en FROM concept c WHERE c.id=f.concept_id))||'%')""",
  "posible mapeo de concepto erróneo (glosa del concepto ausente en los sentidos)"),
 ("PROV · formas sin source_id",
  "SELECT count(*) FROM form WHERE source_id IS NULL",
  "procedencia obligatoria (§0.8 del PLAN)"),
 ("PROV · source_id sin registro en tabla source",
  "SELECT count(*) FROM form f WHERE NOT EXISTS(SELECT 1 FROM source s WHERE s.id=f.source_id)",
  "toda fuente debe estar citada con licencia"),
 ("PROV · aristas de linaje sin registro de fuente",
  "SELECT count(*) FROM form_etymology fe WHERE fe.source_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM source s WHERE s.id=fe.source_id)",
  "procedencia del linaje"),
 ("LIC · protoformas de fuente en cuarentena (aviso, no error)",
  "SELECT count(*) FROM protoform_hypothesis ph JOIN source s ON s.id=ph.source_id WHERE s.redistributable=false",
  "OK internamente; EXCLUIR (redistributable=true) en cualquier export público"),
 ("SEM · formas duplicadas EXACTAS misma fuente no-lexibank",
  """SELECT COALESCE(sum(c-1),0) FROM (SELECT count(*) c FROM form WHERE source_id NOT IN ('lexibank','ids')
     GROUP BY source_id,lect_id,lower(orthography),concept_id,pos HAVING count(*)>1) t""",
  "redundancia real (lexibank/ids se excluyen: su duplicación es agregación legítima)"),
]


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    print("═══ AUDIT DE CALIDAD ═══")
    warn = 0
    for name, sql, note in CHECKS:
        cur.execute(sql)
        n = cur.fetchone()[0]
        flag = "✅" if n == 0 else ("ℹ️ " if name.startswith("LIC") else "⚠️ ")
        if n and not name.startswith("LIC"):
            warn += 1
        print(f"{flag} {name:52s} {n:>8}   {note}")
    print(f"\n{'—'*70}\navisos de calidad (≠0, excl. licencia): {warn}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
