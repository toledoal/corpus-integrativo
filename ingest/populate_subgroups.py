#!/usr/bin/env python3
"""Puebla lect.subgroup (RAMA) desde families.py para las lenguas declaradas (Romance, Germanic, Slavic…).

La 'rama' vive en families.py (romance/germanic/…) pero no estaba en la tabla lect. Esto la copia como etiqueta
legible a lect.subgroup (solo donde estaba NULL, no pisa clasificación Glottolog previa como 'Latino-Faliscan').
Habilita el filtro por Rama en el visor/Meulemans. Cobertura = miembros de families.py; las lenguas de Lexibank
sin rama quedan pendientes (poblar desde Glottolog aparte).

Uso: .venv/bin/python ingest/populate_subgroups.py
"""
import psycopg
from config import DSN
from families import FAMILIES

LABEL = {"romance": "Romance", "germanic": "Germanic", "slavic": "Slavic", "hellenic": "Hellenic",
         "albanian": "Albanian", "armenian": "Armenian", "tocharian": "Tocharian", "anatolian": "Anatolian",
         "celtic": "Celtic", "baltic": "Baltic", "indo-iranian": "Indo-Iranian", "italic": "Italic"}


def main():
    conn = psycopg.connect(DSN); cur = conn.cursor(); n = 0
    for fam, cfg in FAMILIES.items():
        lab = LABEL.get(fam, fam.title())
        for code in cfg["members"]:
            cur.execute("UPDATE lect SET subgroup=%s WHERE id=%s AND (subgroup IS NULL OR subgroup='')", (lab, code))
            n += cur.rowcount
    conn.commit()
    print(f"OK · lect.subgroup poblados = {n}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
