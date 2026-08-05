# Corpus Integrativo — Reporte de estado (Fase 0)

*Piloto Latín + Romance. Fecha: 2026-08-05. Licencia BD: CC BY-SA 4.0.*

## 1. Qué está construido y funcionando

- **Esquema Postgres v0.3** vivo (24 tablas, vistas de linaje y resonancia). `db/schema.sql` + `db/setup_dev.sh`.
- **Ingesta pycldf** (loader único CLDF) — Lexibank Latín+Romance. `ingest/cldf_ingest.py`.
- **Loader Kaikki** (etimología + sentidos + morfología). `ingest/kaikki_ingest.py`.
- **Esqueleto consonántico + vocálico** recomputado limpio (objeto endolingüístico nuestro). `ingest/recompute_skeleton.py`.
- **Inventario de afijos** desde Kaikki. `ingest/affix_extract.py`.
- **Reconciliación de LECTS** por glottocode (Frankenstein de lengua resuelto). `ingest/reconcile_lects.py`.
- **Reconciliación de FORMAS** (solapamiento Lexibank∩Kaikki, no destructiva). `ingest/reconcile_forms.py`.
- **Marcas de calidad** no destructivas (is_proper, core_valid). `ingest/mark_quality.py`.
- **Red de cognación** por etymon compartido. `ingest/build_cognates.py`.
- **Capa criptológica** (operadores Δ conservar/mutar/truncar + firma `crypto` con autoinformación). `ingest/build_correspondences.py`.
- **Rasgos fonológicos** (panphon F₂ⁿ). `ingest/build_features.py`.
- **Red de polisemia** (sentidos de una misma forma). `ingest/build_polysemy.py`.
- **Colexificación** (grafía → ≥2 conceptos). `ingest/build_colex.py`.
- **Proto-formas** (= etymon; latín atestiguado / proto reconstruido). `ingest/build_protoforms.py`.
- **Contacto** (préstamos → cohortes por lengua-fuente). `ingest/build_contact.py`.
- **Suite de QA** (26 checks de regresión, con guardarraíles anti-fuga no-romance). `tests/qa.py`.

## 2. Datos actuales — 18 lenguas romances (piloto COMPLETO)

*Todas las 23 tablas pobladas. QA: 26 OK, 0 fallos.*

| Capa | Cantidad |
|---|---|
| Formas | **442.350** |
| Sentidos (polisemia) | **587.654** |
| Segmentos | 2.173.284 |
| Esqueletos (cons+vocales+CV) | 278.871 |
| Firmas criptológicas (`crypto`) | 278.033 |
| Etimología a nivel de palabra | 225.386 |
| Morfemas | 130.930 |
| **Cognados** (sets / miembros) | **19.870 / 81.526** |
| **Correspondencias** (operadores Δ) | **36.097** |
| **Enlaces de polisemia** | **286.116** |
| **Préstamos** (substrate) / cohortes | **72.947 / 457** |
| **Proto-formas** hipotetizadas | **19.870** |
| **Colexificaciones** | **1.068** |
| Rasgos fonológicos (fonema×rasgo) | 7.320 (305 fonemas) |
| Linajes de esqueleto (resonancia) | 45.906 |
| Afijos | 6.454 |
| Conceptos (Concepticon) | 3.205 |
| Lects | 645 (18 romances + protos/orígenes) |

## 3. Pruebas superadas (Romance)

- **Cifrado mayormente identidad:** 73% conservar · 19% truncar · 8% mutar (nivel-clase OAS) → "symmetry hides history".
- **Cercanía dialectal recuperada:** es↔it conservan 82.5%; el portugués muta más (11%) — refleja su mayor divergencia.
- **Inestabilidad por clase (fonología histórica):** sibilantes **Σ mutan 19.7%**, dentales **Θ 12.3%**; labiales **Φ**
  y líquidas **Λ** las más estables. Λ se pierde por **truncación**, no mutación (coherente con "Λ la más perdida").
- **Contacto real:** cohortes `ro←fr` (galicismos), `ro←cu` (eslavo ecl.), arabismos del español (*aceituna, aceña, achacar*).
- **Anti-apofenia (nulo):** similitud de esqueleto DENTRO de cognados **0.796** vs AZAR **0.297** = **2.68×**;
  solo 0.25% de pares al azar alcanzan la media intra-set → **los cognados son estructura real, no apofenia**.
  (`tests/probe_cognates.py`)
- **QA:** **26 OK, 0 fallos**, con 13 guardarraíles nuevos anti-fuga (ningún lect germánico/eslavo en las capas romance).

## 4. Replicabilidad a otros subsistemas — VERIFICADA

- **Registro de familias** `ingest/families.py`: cada subsistema define `members`, `ancestors` (con status
  atestiguado/reconstruido), `kaikki_files`, `reconcile_pairs`. Romance completo; germánico y eslavo **definidos** (no cargados).
- **Builders parametrizados por `CI_FAMILY`** (default `romance`). Replicar = definir la familia + cargar su Kaikki +
  `CI_FAMILY=germanic ./ingest/build_analytics.sh`.
- **Borrados ACOTADOS a la familia** (antes cada builder hacía `DELETE` de tabla completa → habría borrado Romance al
  correr otra familia). Ahora las familias **coexisten**.
- **Smoke test de aislamiento:** correr `CI_FAMILY=germanic` sin datos germánicos → 0 filas, **Romance intacto**. ✔
- **Determinista:** dos corridas → mismos conteos (19.870 sets).
- **Hallazgos del refactor:** el filtro por familia destapó `neap1235` (283 formas napolitanas sin reconciliar → ahora
  fusionadas en `nap`) y la fila-semilla `de·Angst` (germánica, correctamente excluida).

## 5. Huecos honestos y siguiente paso

1. **Latinismos como `prestamo`:** los cultismos entran como préstamo (correcto), pero conviene marca `learned` a futuro.
2. **Formas multipalabra de Kaikki** (refranes) inflan la autoinformación → candidata marca `is_phrase`.
3. **Colexificación** limitada a formas con `concept_id` (Lexibank, 19k) — declarado; crecerá al mapear más sentido.
4. **QA 2-ciclos** aún a nivel lengua (préstamos bidireccionales legítimos) → mover a nivel palabra.
5. **Acento/prosodia** capturado en `segment.is_stressed`; falta explotarlo en estudios tonales.

**Siguiente:** correr las pruebas del usuario sobre estas capas, y —solo cuando Romance esté validado— **replicar a Germánico**
(cargar Kaikki germánico + `CI_FAMILY=germanic ./ingest/build_analytics.sh`).

## 6. Hardening / revisión de código profunda (para escalar a miles de lenguas)

Dos revisores adversariales (performance + correctitud) + verificación propia → arreglos por prioridad de escala,
todos con QA 26 OK/0 y en GitHub (`github.com/toledoal/corpus-integrativo`, commits por lotes):

1. **Esquema reproducible** — `form_etymology` y 8 columnas que se creaban por `ALTER` en runtime ahora en `schema.sql`
   (validado en DB limpia) + `db/migrate_0.4.sql`.
2. **Aislamiento por familia** — tablas analíticas etiquetadas por `family` (id `cog:<familia>:…`, borrado por familia
   vía CASCADE); `crypto.self_info` con unigrama global (idempotente). Probado: correr `italic` deja `romance` intacto.
3. **11+ índices** en las columnas de borrado/join (form(source_id), correspondence, form_etymology(kind)…).
4. **COPY masivo** en todos los loops calientes → pipeline analítico completo en ~30 s.
5. **Config central** `ingest/config.py` (DSN + rutas por `CI_DSN`/`CI_KAIKKI_DIR`); cero hardcode en 19 archivos.
6. **Coexistencia**: comma-codes saltados (22 lects-basura limpiados), `affix`/`core_skeleton` acotados por lengua,
   rename de PK seguro en `reconcile_lects`, QA family-aware.
7. **Alta ordenada de familia**: `ingest/add_family.sh` + `families.load_plan()` (protos con `--all`) +
   `RUNBOOK-agregar-familia.md`. Germánico/Eslavo con su proto declarado (no cargados).
8. **Afinado**: NW memoizado + short-circuit, selección de representante determinista (`ORDER BY`),
   `recompute_skeleton --only-new` incremental.
