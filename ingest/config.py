#!/usr/bin/env python3
"""Config central del Corpus Integrativo — conexión y rutas por variable de entorno (CERO hardcode).

Todo script de ingesta/QA importa de aquí. Sobrescribir sin tocar código:
    export CI_DSN="host=/var/run/postgresql port=5432 user=me dbname=corpus"
    export CI_KAIKKI_DIR=/datos/kaikki/dict

Así el mismo pipeline corre en el clúster local del proyecto, en otro servidor, o en CI, sin editar fuentes.
"""
import os

# Conexión a Postgres (default: clúster local del proyecto por socket UNIX)
DSN = os.environ.get(
    "CI_DSN",
    "host=/tmp/ci_pg port=5433 user=postgres dbname=corpus_integrativo",
)

# Diccionarios Kaikki (JSONL por lengua). Default: relativo al repo (../../data/lexicon/kaikki/dict)
KDIR = os.environ.get(
    "CI_KAIKKI_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "lexicon", "kaikki", "dict")),
)
