#!/usr/bin/env python3
"""Mide el efecto de la regla BICLASE sobre la CONSERVACIÓN del código entre coderivados, POR FAMILIA.

El documento oas-segmentos-biclase §6 predice: la conservación DEBE AUMENTAR con biclase (shall=skal). Pero
Alejandro advierte que en eslavo (y otras) la š no siempre viene de *sk (RUKI, palatalización) → biclase podría
REDUCIRLA. Esto lo decide la genealogía, no la superficie → se MIDE, no se asume.

Métrica: dentro de cada cognate_set, cobertura del código MODAL = (miembros con el código más común)/(total).
Promedio por familia, calculado con biclase (compute(..,True)) y sin (compute(..,False)). Δ>0 = biclase ayuda.

Uso: .venv/bin/python analysis/biclass_conservation.py
"""
import sys
sys.path.insert(0, "ingest")
from collections import defaultdict, Counter
import psycopg
from config import DSN
from recompute_skeleton import compute


def code_of(segs, biclass):
    if not segs:
        return None
    _, code, _, _, _ = compute(segs, biclass=biclass)
    return code


def coverage(codes):
    codes = [c for c in codes if c]
    if len(codes) < 2:
        return None
    modal = Counter(codes).most_common(1)[0][1]
    return modal / len(codes)


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor()
    cur.execute("""SELECT cs.family, cm.cognate_set_id, f.segments_raw
                   FROM cognate_member cm JOIN cognate_set cs ON cs.id=cm.cognate_set_id
                   JOIN form f ON f.id=cm.form_id
                   WHERE f.segments_raw IS NOT NULL AND cs.family IS NOT NULL""")
    sets_bi = defaultdict(lambda: defaultdict(list))   # family -> set -> [code_biclass]
    sets_no = defaultdict(lambda: defaultdict(list))
    for fam, sid, segs in cur.fetchall():
        sets_bi[fam][sid].append(code_of(segs, True))
        sets_no[fam][sid].append(code_of(segs, False))

    print(f"{'familia':<10}{'sets':>7}{'cobertura SIN':>15}{'cobertura BICLASE':>19}{'Δ':>9}   veredicto")
    print("─" * 78)
    for fam in sorted(sets_bi):
        cov_no = [coverage(v) for v in sets_no[fam].values()]
        cov_bi = [coverage(v) for v in sets_bi[fam].values()]
        cov_no = [c for c in cov_no if c is not None]
        cov_bi = [c for c in cov_bi if c is not None]
        if not cov_bi:
            continue
        mno = sum(cov_no) / len(cov_no); mbi = sum(cov_bi) / len(cov_bi)
        delta = mbi - mno
        verdict = "biclase AYUDA ✓" if delta > 0.002 else ("biclase DAÑA ✗" if delta < -0.002 else "neutro")
        print(f"{fam:<10}{len(cov_bi):>7}{mno:>15.4f}{mbi:>19.4f}{delta:>+9.4f}   {verdict}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
