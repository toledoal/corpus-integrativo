# Corpus Integrativo · base de datos (Fase 0)

PostgreSQL 18. Esquema v0.3 (`schema.sql`) + seed de validación (`seed_examples.sql`). Licencia de la BD: **CC BY-SA 4.0**.

## Arrancar / cargar (clúster local del proyecto, aislado)
```bash
bash db/setup_dev.sh          # initdb + arranca (puerto 5433, socket /tmp/ci_pg) + carga schema.sql
# seed de ejemplos:
/opt/homebrew/opt/postgresql@18/bin/psql -h /tmp/ci_pg -p 5433 -U postgres -d corpus_integrativo -f db/seed_examples.sql
```
Conectar:
```bash
/opt/homebrew/opt/postgresql@18/bin/psql -h /tmp/ci_pg -p 5433 -U postgres -d corpus_integrativo
```
Detener:
```bash
/opt/homebrew/opt/postgresql@18/bin/pg_ctl -D db/pgdata stop
```
(`db/pgdata/` y `db/sock/` están en `.gitignore` — no se versionan.)

## Qué hay (22 tablas, 2 vistas, 6 enums)
- **Genealogía:** `lect` (escalera de niveles), `ancestry_edge` (grafo probabilístico: kind/law_class/prob/status/
  crosses_macrosystem), `protoform_hypothesis` (PIE plural), `cognate_set`+`cognate_member` (cognación, condicional).
- **Forma/fonética:** `form`, `segment`, `feature`.
- **Morfología:** `morph` (root/affix/pattern), `affix` (afijos como entradas-morfema).
- **Sentido:** `sense`, `polyseme_link`, `colex`, `concept` (nodo entre lenguas).
- **Contacto:** `contact_cohort`+`cohort_member`, `substrate_edge`.
- **Endo/cripto:** `skeleton` (por-estadio), `skeleton_lineage` (resonancia), `correspondence` (conservar/mutar/truncar),
  `crypto`.
- **Fuentes:** `source` (con `license`+`redistributable` para cuarentena NC/ND).
- **Vistas:** `v_lineage` (CTE recursiva = "toda la historia de la palabra"), `v_resonance` (mismo código de esqueleto
  entre ramas).

## Consultas de validación (ver seed)
1. Linaje: `SELECT * FROM v_lineage WHERE start_lect='es' ORDER BY depth;`
2. PIE plural: `protoform_hypothesis` del etymon de una forma.
3. Resonancia: `SELECT * FROM v_resonance;`
4. Cognados+esqueleto de un `cognate_set`.

## Pendiente Fase 0
- Ingesta desde **Kaikki** (Latín + Romances) → poblar `form/segment/sense/morph`.
- Recomputar **skeltree** limpio desde el núcleo → poblar `skeleton`.
- Cargar iecor (cognación oro) + LIV² (protos).
- Acento: hueco (StressTyp2 es ND; sacar de corpus acentuados/dicc.).
