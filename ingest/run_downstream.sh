#!/bin/bash
# Pipeline downstream tras cargar Kaikki: segmentar → esqueleto → afijos → core → reconciliar formas.
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
ROMANCE="Latin Spanish Italian French Portuguese Catalan Romanian Galician Occitan Sardinian Sicilian Neapolitan Aromanian Friulian Ladin Walloon Old_French Old_Spanish"
echo "=== 1/5 segmentar IPA Kaikki ==="; $PY ingest/segment_kaikki.py
echo "=== 2/5 recomputar esqueleto ==="; $PY ingest/recompute_skeleton.py
echo "=== 3/5 extraer afijos ==="; $PY ingest/affix_extract.py $ROMANCE
echo "=== 4/5 core_skeleton ==="; $PY ingest/core_skeleton.py
echo "=== 5/5 reconciliar formas ==="; $PY ingest/reconcile_forms.py
echo "DOWNSTREAM DONE"
