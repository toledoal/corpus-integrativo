#!/usr/bin/env python3
"""Suite de QA del Corpus Integrativo — red de seguridad para cachar errores (y evitar el Frankenstein).

Corre una batería de checks sobre la BD y reporta OK / ⚠️ / ✗ por cada uno. Pensado para correr repetidamente
(regresión) — sobre todo ANTES y DESPUÉS de reconciliar fuentes. Categorías: integridad, duplicación/reconciliación,
esqueleto, vocales, etimología (grafo), concepto, consistencia entre fuentes, procedencia/licencia.

Uso: .venv/bin/python tests/qa.py
"""
import psycopg

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "ingest"))
from config import DSN

# (nombre, sql→devuelve un entero de VIOLACIONES, severidad, nota)
#   severidad: 'fail' (>0 = ✗), 'warn' (>0 = ⚠️), 'info' (solo reporta)
CHECKS = [
    # --- integridad referencial / campos obligatorios ---
    ("INT · formas sin lect", "SELECT count(*) FROM form WHERE lect_id IS NULL", "fail", "toda forma pertenece a un lect"),
    ("INT · formas sin fuente", "SELECT count(*) FROM form WHERE source_id IS NULL", "fail", "procedencia obligatoria (cumplimiento CC)"),
    ("INT · skeleton huérfano", "SELECT count(*) FROM skeleton s LEFT JOIN form f ON f.id=s.form_id WHERE f.id IS NULL", "fail", "skeleton apunta a forma inexistente"),
    ("INT · sense huérfano", "SELECT count(*) FROM sense s LEFT JOIN form f ON f.id=s.form_id WHERE f.id IS NULL", "fail", ""),
    # --- DUPLICACIÓN / FRANKENSTEIN ---
    ("DUP · misma (lengua,grafía) en >1 fuente", "SELECT count(*) FROM (SELECT lect_id, lower(orthography) o FROM form WHERE orthography IS NOT NULL GROUP BY 1,2 HAVING count(DISTINCT source_id)>1) t", "warn", "candidatos a RECONCILIAR (nodos sueltos de la misma palabra)"),
    ("DUP · misma (lengua,grafía) misma fuente >1", "SELECT count(*) FROM (SELECT lect_id, lower(orthography), source_id FROM form WHERE orthography IS NOT NULL GROUP BY 1,2,3 HAVING count(*)>1) t", "warn", "duplicados intra-fuente (¿homónimos/POS?)"),
    # --- ESQUELETO ---
    ("SKEL · residual '?' en código", "SELECT count(*) FROM skeleton WHERE code ~ '\\?' OR cv_template ~ '\\?'", "fail", "segmento sin clasificar (¿marcador no manejado?)"),
    ("SKEL · nasal sin normalizar", "SELECT count(*) FROM skeleton WHERE cons_skeleton ~ '[ŋɲɳɴɱ]'", "fail", "superficie no canonizada a n/m"),
    ("SKEL · #símbolos ≠ #consonantes", "SELECT count(*) FROM skeleton WHERE code IS NOT NULL AND array_length(string_to_array(code,'·'),1) <> array_length(string_to_array(cons_skeleton,'·'),1)", "fail", "código de clase y letras descuadrados"),
    ("SKEL · #C(cv) ≠ #consonantes", "SELECT count(*) FROM skeleton WHERE cons_skeleton IS NOT NULL AND (length(cv_template)-length(replace(cv_template,'C',''))) <> array_length(string_to_array(cons_skeleton,'·'),1)", "fail", "cv_template inconsistente con cons_skeleton"),
    # --- VOCALES ---
    ("VOW · #V(cv) ≠ #vocales", "SELECT count(*) FROM skeleton WHERE vowels IS NOT NULL AND (length(cv_template)-length(replace(cv_template,'V',''))) <> array_length(string_to_array(vowels,'·'),1)", "fail", "vocales perdidas/descuadradas"),
    ("VOW · segmentos perdidos (cv≠#segmentos)", "SELECT count(*) FROM skeleton s JOIN form f ON f.id=s.form_id WHERE f.segments_raw IS NOT NULL AND length(s.cv_template) <> coalesce(array_length(f.segments_raw,1),0)", "fail", "cada segmento debe aparecer en cv_template (nada se pierde)"),
    # --- ETIMOLOGÍA (grafo) ---
    ("ETY · self-loops de lengua", "SELECT count(*) FROM ancestry_edge WHERE child_lect=parent_lect", "fail", "una lengua no desciende de sí misma"),
    ("ETY · 2-ciclos (A→B y B→A)", "SELECT count(*) FROM ancestry_edge a JOIN ancestry_edge b ON a.child_lect=b.parent_lect AND a.parent_lect=b.child_lect WHERE a.child_lect<a.parent_lect", "warn", "ciclo genealógico (imposible en herencia)"),
    ("ETY · child más VIEJO que parent", "SELECT count(*) FROM ancestry_edge e JOIN lect c ON c.id=e.child_lect JOIN lect p ON p.id=e.parent_lect WHERE c.date_hi IS NOT NULL AND p.date_lo IS NOT NULL AND c.date_hi < p.date_lo", "warn", "cronología imposible (hija anterior a la madre)"),
    ("ETY · form_etymology huérfano", "SELECT count(*) FROM form_etymology fe LEFT JOIN form f ON f.id=fe.child_form_id WHERE f.id IS NULL", "fail", ""),
    # --- CONCEPTO ---
    ("CPT · formas sin concepto", "SELECT count(*) FROM form WHERE concept_id IS NULL", "info", "cobertura Concepticon (Kaikki aún sin mapear)"),
    # --- MARCAS de calidad (informativas: se MARCA, NO se filtra ni se borra) ---
    ("MARK · core_skeleton sospechoso", "SELECT count(*) FROM skeleton WHERE core_valid=false", "info", "core no ⊆ palabra (base arrastra su terminación) — CONSERVADO y marcado"),
    ("MARK · nombres propios (heurística)", "SELECT count(*) FROM form WHERE is_proper", "info", "inicial mayúscula — marcado, NO filtrado (el corpus crece)"),
    # --- RED DE COGNACIÓN / CRIPTOLOGÍA (capas relacionales) ---
    ("COG · cognate_member huérfano", "SELECT count(*) FROM cognate_member cm LEFT JOIN form f ON f.id=cm.form_id WHERE f.id IS NULL", "fail", "miembro apunta a forma inexistente"),
    ("COG · set con <2 miembros", "SELECT count(*) FROM (SELECT cognate_set_id FROM cognate_member GROUP BY 1 HAVING count(*)<2) t", "fail", "un cognado necesita ≥2 reflejos"),
    ("COG · miembro NO romance (FUGA)", "SELECT count(*) FROM cognate_member cm JOIN form f ON f.id=cm.form_id WHERE f.lect_id <> ALL(ARRAY['la','es','it','fr','pt','ca','ro','gl','oc','sc','scn','nap','rup','fur','lld','wa','fro','osp'])", "fail", "SOLO Romance por ahora (no germánico/eslavo)"),
    ("CORR · lect NO romance (FUGA)", "SELECT count(*) FROM correspondence WHERE from_lect <> ALL(ARRAY['la','es','it','fr','pt','ca','ro','gl','oc','sc','scn','nap','rup','fur','lld','wa','fro','osp']) OR to_lect <> ALL(ARRAY['la','es','it','fr','pt','ca','ro','gl','oc','sc','scn','nap','rup','fur','lld','wa','fro','osp'])", "fail", "SOLO Romance por ahora"),
    ("CRY · crypto huérfano", "SELECT count(*) FROM crypto c LEFT JOIN form f ON f.id=c.form_id WHERE f.id IS NULL", "fail", "firma apunta a forma inexistente"),
    ("FEAT · fonema sin rasgos", "SELECT count(DISTINCT phoneme) FROM feature", "info", "fonemas romance con matriz panphon"),
    ("FEAT · valor fuera de {-1,0,1}", "SELECT count(*) FROM feature WHERE value NOT IN (-1,0,1)", "fail", "rasgo debe ser ternario"),
    ("POLY · enlace a sentido inexistente", "SELECT count(*) FROM polyseme_link pl LEFT JOIN sense s ON s.id=pl.sense_a WHERE s.id IS NULL", "fail", ""),
    ("POLY · lect NO romance (FUGA)", "SELECT count(*) FROM polyseme_link WHERE lect_id IS NOT NULL AND lect_id <> ALL(ARRAY['la','es','it','fr','pt','ca','ro','gl','oc','sc','scn','nap','rup','fur','lld','wa','fro','osp'])", "fail", "SOLO Romance por ahora"),
    ("COLX · lect NO romance (FUGA)", "SELECT count(*) FROM colex WHERE lect_id IS NOT NULL AND lect_id <> ALL(ARRAY['la','es','it','fr','pt','ca','ro','gl','oc','sc','scn','nap','rup','fur','lld','wa','fro','osp'])", "fail", "SOLO Romance por ahora"),
    ("PROTO · set inexistente", "SELECT count(*) FROM protoform_hypothesis ph LEFT JOIN cognate_set cs ON cs.id=ph.cognate_set_id WHERE cs.id IS NULL", "fail", "hipótesis sobre cognate_set fantasma"),
    ("SUBS · forma-hija NO romance (FUGA)", "SELECT count(*) FROM substrate_edge se JOIN form f ON f.id=se.form_id WHERE f.lect_id <> ALL(ARRAY['la','es','it','fr','pt','ca','ro','gl','oc','sc','scn','nap','rup','fur','lld','wa','fro','osp'])", "fail", "préstamo debe ENTRAR a un lect romance (la fuente sí puede ser externa)"),
    ("SUBS · substrate huérfano", "SELECT count(*) FROM substrate_edge se LEFT JOIN form f ON f.id=se.form_id WHERE f.id IS NULL", "fail", ""),
    # --- PROCEDENCIA / LICENCIA ---
    ("LIC · forma de fuente NO redistribuible", "SELECT count(*) FROM form f JOIN source s ON s.id=f.source_id WHERE s.redistributable=false", "fail", "cuarentena NC/ND no debe entrar a la BD redistribuible"),
]

# checks con MUESTRA (para inspección humana)
SAMPLES = {
    "DUP · misma (lengua,grafía) en >1 fuente":
        "SELECT lect_id, lower(orthography) AS grafia, string_agg(DISTINCT source_id,',') AS fuentes, count(*) FROM form WHERE orthography IS NOT NULL GROUP BY 1,2 HAVING count(DISTINCT source_id)>1 ORDER BY 4 DESC LIMIT 6",
    "SKEL · #símbolos ≠ #consonantes":
        "SELECT f.orthography, s.cons_skeleton, s.code FROM skeleton s JOIN form f ON f.id=s.form_id WHERE array_length(string_to_array(s.code,'·'),1) <> array_length(string_to_array(s.cons_skeleton,'·'),1) LIMIT 5",
}


def spotchecks(cur):
    """asserts sobre palabras conocidas (Lexibank)."""
    expect = [("lexibank:iecor-112-narrow-1", "Ξ·Χ·Σ·Θ·Σ", "angustus")]
    out = []
    for fid, code, name in expect:
        cur.execute("SELECT code FROM skeleton WHERE form_id=%s", (fid,))
        r = cur.fetchone()
        ok = r and r[0] == code
        out.append((f"SPOT · {name} = {code}", 0 if ok else 1, "fail",
                    f"obtenido: {r[0] if r else 'NADA'}"))
    return out


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    checks = list(CHECKS)
    rows = []
    for name, sql, sev, note in checks:
        cur.execute(sql); v = cur.fetchone()[0]
        rows.append((name, v, sev, note))
    for name, v, sev, note in spotchecks(cur):
        rows.append((name, v, sev, note))

    npass = nwarn = nfail = 0
    print(f"{'CHECK':<44}{'VIOL':>8}  VERDICTO  NOTA")
    print("─" * 100)
    for name, v, sev, note in rows:
        if sev == "info":
            mark = "ℹ️ "
        elif v == 0:
            mark = "✅"; npass += 1
        elif sev == "warn":
            mark = "⚠️ "; nwarn += 1
        else:
            mark = "❌"; nfail += 1
        print(f"{name:<44}{v:>8}  {mark:<8}  {note}")
    print("─" * 100)
    print(f"OK={npass}  ⚠️={nwarn}  ❌={nfail}")

    for name, sql in SAMPLES.items():
        cur.execute(sql); s = cur.fetchall()
        if s:
            print(f"\n  ▸ muestra [{name}]:")
            for r in s:
                print("     ", r)
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
