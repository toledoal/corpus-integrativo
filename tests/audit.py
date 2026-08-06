#!/usr/bin/env python3
"""AUDITORÍA de la base — ¿están todos los campos funcionando y los datos que buscamos bien?

Complementa `qa.py` (violaciones de integridad) con COMPLETITUD y SANIDAD:
  1. Censo de tablas (todas pobladas; ninguna vacía por error).
  2. Completitud de campos (fill-rate por columna en form/skeleton — ¿se llenan?).
  3. Cobertura de capas por familia (forma→ipa→esqueleto→sentido→etimología→cognado).
  4. End-to-end: una forma con TODAS sus capas conectadas (prueba que el pipeline enlaza).
  5. Sanidad de datos: consultas clave (resonancia, código, correspondencia) devuelven lo esperado.

Uso: .venv/bin/python tests/audit.py
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "ingest"))
import psycopg
from config import DSN


def q1(cur, sql, p=()):
    cur.execute(sql, p); r = cur.fetchone(); return r[0] if r else None


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()

    print("═" * 70 + "\n1 · CENSO DE TABLAS\n" + "═" * 70)
    cur.execute("SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC")
    for t, n in cur.fetchall():
        flag = "  ⚠️ VACÍA" if n == 0 else ""
        print(f"  {t:<24}{n:>12,}{flag}")

    print("\n" + "═" * 70 + "\n2 · COMPLETITUD DE CAMPOS (fill-rate)\n" + "═" * 70)
    checks = {
        "form": ["orthography", "ipa_raw", "ipa_elab", "segments_raw", "etymology_text", "pos", "concept_id", "is_proper"],
        "skeleton": ["cons_skeleton", "code", "core_skeleton", "vowels", "cv_template", "skeleton_lineage_id", "core_valid"],
        "segment": ["ipa", "syllable", "is_stressed"],
        "sense": ["gloss", "concept_id"],
        "cognate_set": ["family", "ancestor_lect", "label"],
        "correspondence": ["a", "b", "env", "corr_type", "family"],
        "crypto": ["feature_vectors", "self_info", "skeleton_id"],
    }
    for tbl, cols in checks.items():
        total = q1(cur, f"SELECT count(*) FROM {tbl}")
        print(f"  {tbl}  (n={total:,})")
        for c in cols:
            nn = q1(cur, f"SELECT count(*) FROM {tbl} WHERE {c} IS NOT NULL")
            pct = 100 * nn / total if total else 0
            bar = "█" * int(pct / 5)
            print(f"    {c:<20}{pct:>5.0f}%  {bar}")

    print("\n" + "═" * 70 + "\n3 · COBERTURA DE CAPAS POR FAMILIA\n" + "═" * 70)
    import families
    fam_lects = {name: cfg["members"] for name, cfg in families.FAMILIES.items()}
    print(f"  {'familia':<14}{'formas':>9}{'con IPA':>9}{'esquel.':>9}{'sentido':>9}{'etimol.':>9}{'cognado':>9}")
    for fam, lects in fam_lects.items():
        base = "FROM form f WHERE f.lect_id = ANY(%s)"
        forms = q1(cur, f"SELECT count(*) {base}", (lects,))
        if not forms:
            continue
        ipa = q1(cur, f"SELECT count(*) {base} AND COALESCE(ipa_raw,ipa_elab) IS NOT NULL", (lects,))
        skel = q1(cur, f"SELECT count(DISTINCT f.id) FROM form f JOIN skeleton s ON s.form_id=f.id WHERE f.lect_id=ANY(%s)", (lects,))
        sens = q1(cur, f"SELECT count(DISTINCT f.id) FROM form f JOIN sense s ON s.form_id=f.id WHERE f.lect_id=ANY(%s)", (lects,))
        ety = q1(cur, f"SELECT count(DISTINCT f.id) FROM form f JOIN form_etymology e ON e.child_form_id=f.id WHERE f.lect_id=ANY(%s)", (lects,))
        cog = q1(cur, f"SELECT count(DISTINCT f.id) FROM form f JOIN cognate_member m ON m.form_id=f.id WHERE f.lect_id=ANY(%s)", (lects,))
        pc = lambda x: f"{100*x/forms:.0f}%"
        print(f"  {fam:<14}{forms:>9,}{pc(ipa):>9}{pc(skel):>9}{pc(sens):>9}{pc(ety):>9}{pc(cog):>9}")

    print("\n" + "═" * 70 + "\n4 · END-TO-END (una forma con todas sus capas)\n" + "═" * 70)
    cur.execute("""SELECT f.id, f.lect_id, f.orthography, COALESCE(f.ipa_raw,f.ipa_elab),
                   sk.cons_skeleton, sk.code, sk.vowels,
                   (SELECT gloss FROM sense s WHERE s.form_id=f.id LIMIT 1),
                   (SELECT count(*) FROM segment g WHERE g.form_id=f.id),
                   (SELECT count(*) FROM cognate_member m WHERE m.form_id=f.id),
                   c.self_info
                   FROM form f JOIN skeleton sk ON sk.form_id=f.id LEFT JOIN crypto c ON c.form_id=f.id
                   WHERE f.orthography='padre' AND f.lect_id='es' LIMIT 1""")
    r = cur.fetchone()
    if r:
        labels = ["id", "lect", "grafía", "ipa", "cons_skeleton", "code", "vocales", "glosa",
                  "#segmentos", "#cognados", "self_info"]
        for lbl, val in zip(labels, r):
            print(f"  {lbl:<14}: {val}")

    print("\n" + "═" * 70 + "\n5 · SANIDAD DE DATOS (consultas clave)\n" + "═" * 70)
    sanity = [
        ("resonancia: nº de lenguas con el código Φ·Θ·Λ (raíz 'padre')",
         "SELECT count(DISTINCT f.lect_id) FROM skeleton sk JOIN form f ON f.id=sk.form_id WHERE sk.code='Φ·Θ·Λ'", None),
        ("códigos distintos en el corpus", "SELECT count(*) FROM skeleton_lineage", None),
        ("formas con esqueleto Y sentido Y etimología",
         "SELECT count(*) FROM form f WHERE EXISTS(SELECT 1 FROM skeleton s WHERE s.form_id=f.id) "
         "AND EXISTS(SELECT 1 FROM sense s WHERE s.form_id=f.id) AND EXISTS(SELECT 1 FROM form_etymology e WHERE e.child_form_id=f.id)", None),
        ("cognados con reflejos en ≥3 lenguas",
         "SELECT count(*) FROM (SELECT cm.cognate_set_id FROM cognate_member cm JOIN form f ON f.id=cm.form_id GROUP BY 1 HAVING count(DISTINCT f.lect_id)>=3) t", None),
        ("correspondencias conservar/mutar/truncar (las 3 presentes)",
         "SELECT count(DISTINCT corr_type) FROM correspondence", None),
        ("self_info: min/media/max",
         "SELECT round(min(self_info),1)||' / '||round(avg(self_info),1)||' / '||round(max(self_info),1) FROM crypto", None),
    ]
    for label, sql, p in sanity:
        try:
            print(f"  {label:<52}= {q1(cur, sql, p or ())}")
        except Exception as ex:
            print(f"  {label:<52}= ERROR {str(ex)[:40]}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
