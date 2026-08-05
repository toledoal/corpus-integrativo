#!/bin/bash
# Clúster Postgres LOCAL del proyecto (aislado; puerto 5433; socket en el dir del proyecto).
# Uso: bash db/setup_dev.sh   (desde corpus_integrativo/)
set -e
PGBIN=/opt/homebrew/opt/postgresql@18/bin
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PGDATA="$HERE/db/pgdata"
SOCK="/tmp/ci_pg"          # socket corto (el path del proyecto excede el máximo de 103 bytes)
PORT=5433
export PGHOST="$SOCK"
mkdir -p "$SOCK"

if [ ! -d "$PGDATA/base" ]; then
  echo "· initdb (clúster nuevo)…"
  "$PGBIN/initdb" -D "$PGDATA" -U postgres --auth=trust >/dev/null
fi

if ! "$PGBIN/pg_isready" -h "$SOCK" -p $PORT >/dev/null 2>&1; then
  echo "· arrancando servidor (puerto $PORT)…"
  "$PGBIN/pg_ctl" -D "$PGDATA" -o "-p $PORT -k $SOCK -c listen_addresses=''" -l "$PGDATA/server.log" -w start
fi

"$PGBIN/psql" -h "$SOCK" -p $PORT -U postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname='corpus_integrativo'" | grep -q 1 \
  || "$PGBIN/createdb" -h "$SOCK" -p $PORT -U postgres corpus_integrativo

echo "· cargando esquema…"
"$PGBIN/psql" -h "$SOCK" -p $PORT -U postgres -d corpus_integrativo -v ON_ERROR_STOP=1 -q -f "$HERE/db/schema.sql"
echo "· OK. Conectar:  $PGBIN/psql -h $SOCK -p $PORT -U postgres -d corpus_integrativo"
