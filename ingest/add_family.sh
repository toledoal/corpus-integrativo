#!/usr/bin/env bash
# ============================================================================
# Alta ORDENADA de una familia / rama lingüística en el Corpus Integrativo.
#
#   ./ingest/add_family.sh <familia>
#
# Requisitos previos (manuales, una vez):
#   1. Declarar la familia en ingest/families.py: members, ancestors (con PROTOS),
#      kaikki_files (nombre de archivo Kaikki → código de lect), reconcile_pairs.
#   2. Tener los .jsonl de Kaikki en $CI_KAIKKI_DIR (descargar de kaikki.org los que falten).
#
# Este script hace, EN ORDEN:
#   A. carga lenguas normales (con etimología)           → kaikki_ingest
#   B. carga ancestros/protos (sin etimología, --all)    → kaikki_ingest --all
#   C. deriva el objeto endolingüístico                  → segment → skeleton → ortho → afijos → core
#   D. reconcilia lects y formas duplicadas              → reconcile_lects / reconcile_forms
#   E. marca calidad (no destructivo)                    → mark_quality
#   F. construye las capas analíticas de ESA familia     → build_analytics.sh (CI_FAMILY)
#   G. QA
# Todo es acotado por familia / lengua: NO pisa otras familias ya cargadas.
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
FAM="${1:?uso: ./ingest/add_family.sh <familia>   (romance|italic|germanic|slavic|…)}"

NORMAL=$($PY ingest/families.py "$FAM" normal)
ANCESTOR=$($PY ingest/families.py "$FAM" ancestor)
echo "════════ ALTA DE FAMILIA: $FAM ════════"
echo "  normales : $NORMAL"
echo "  ancestros: $ANCESTOR   (se cargan con --all)"

echo "── A. carga lenguas normales ──"
if [ -n "$NORMAL" ]; then $PY ingest/kaikki_ingest.py $NORMAL; else echo "  (sin lenguas normales)"; fi

echo "── B. carga ancestros/protos (--all) ──"
if [ -n "$ANCESTOR" ]; then $PY ingest/kaikki_ingest.py $ANCESTOR --all; else echo "  (sin ancestros)"; fi

echo "── C. objeto endolingüístico (segmentar → esqueleto → ortográfico → afijos → core) ──"
$PY ingest/segment_kaikki.py
$PY ingest/recompute_skeleton.py --only-new    # incremental: no reprocesa esqueletos de otras familias
[ -n "$ANCESTOR" ] && $PY ingest/skeleton_from_ortho.py || true   # protos/antiguas sin IPA → esqueleto ortográfico
$PY ingest/affix_extract.py $NORMAL $ANCESTOR
$PY ingest/core_skeleton.py $NORMAL $ANCESTOR

echo "── D. reconciliación (lects duplicados por glottocode + formas Lexibank∩Kaikki) ──"
$PY ingest/reconcile_lects.py
$PY ingest/reconcile_forms.py

echo "── E. marcas de calidad (no destructivo) ──"
$PY ingest/mark_quality.py

echo "── F. capas analíticas de la familia ──"
CI_FAMILY="$FAM" ./ingest/build_analytics.sh

echo "════════ $FAM cargada. Revisa la QA arriba. ════════"
