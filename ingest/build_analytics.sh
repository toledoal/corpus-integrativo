#!/usr/bin/env bash
# Construye TODAS las capas analíticas/relacionales para la familia CI_FAMILY (default 'romance').
# Replicar a otra familia:  CI_FAMILY=germanic ./ingest/build_analytics.sh
# (requiere que esa familia esté definida en ingest/families.py y sus datos Kaikki ya cargados)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
echo "════════ CAPAS ANALÍTICAS · familia=${CI_FAMILY:-romance} ════════"
$PY ingest/build_cognates.py
$PY ingest/build_correspondences.py
$PY ingest/build_features.py
$PY ingest/build_polysemy.py
$PY ingest/build_colex.py
$PY ingest/build_protoforms.py
$PY ingest/build_contact.py
echo "════════ QA ════════"
$PY tests/qa.py | grep -E "OK=|❌|FUGA"
