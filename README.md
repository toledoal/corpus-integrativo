# Corpus Integrativo

Una base de datos lingüística **multi-capa y multi-estadio** que reúne, para cada palabra, su
**forma, fonética, prosodia, morfología, sentido, genealogía y objetos derivados** (esqueleto
consonántico endolingüístico + firma criptológica) en un solo modelo relacional consultable.

El objetivo es resolver el cuello de botella de los corpus comparativos: los recursos existentes o
son *densos pero sin cognación fiable* (Lexibank), o son *oro pero delgados* (iecor, Swadesh ~130), y
**ninguno trae acento, prosodia, morfología ni sub-ramas dentro del dato**. Aquí todo eso vive en el
mismo lugar, con procedencia por fila y sin tirar nada (se **marca**, no se filtra).

> **Estado actual:** piloto **Romance completo** — 18 lenguas romances + latín, las 23 tablas pobladas,
> todas las capas analíticas construidas, QA en verde. Rama **itálica** añadida (variedades de latín
> tipadas, Umbro y Proto-Itálico). Diseñado para **escalar a miles de lenguas** de cualquier familia.

---

## Qué contiene (las capas)

| Capa | Tablas | Qué guarda |
|---|---|---|
| **Forma** | `form`, `segment` | grafía, IPA, segmentos con sílaba y **acento** |
| **Fonología** | `skeleton`, `skeleton_lineage`, `feature` | esqueleto consonántico OAS (código de clase Φ·Θ·Χ·Σ·Λ·Ϻ·Ξ), vocales, plantilla CV, rasgos panphon F₂ⁿ |
| **Morfología** | `morph`, `affix` | raíz / afijo / patrón; núcleo sin afijos (`core_skeleton`) |
| **Sentido** | `sense`, `concept`, `polyseme_link`, `colex` | glosas, conceptos Concepticon, red de polisemia intra-lengua, colexificación |
| **Genealogía** | `lect`, `ancestry_edge`, `form_etymology`, `protoform_hypothesis` | árbol de lenguas/estadios, etimología palabra→palabra, proto-formas con status atestiguado/reconstruido |
| **Cognación** | `cognate_set`, `cognate_member` | familias cognadas agrupadas por etymon compartido |
| **Criptología** | `correspondence`, `crypto` | operadores de cambio (conservar/mutar/truncar) y firma por forma (autoinformación) |
| **Contacto** | `substrate_edge`, `contact_cohort`, `cohort_member` | préstamos y cohortes por lengua-fuente (p. ej. arabismos) |
| **Procedencia** | `source` | licencia y atribución obligatoria por fuente |

Las **cuatro redes** que atraviesan el corpus: cognación (forma), polisemia (sentido intra-lengua),
concepto (sentido entre lenguas), y cohorte de contacto (préstamo).

---

## Arquitectura

```
FUENTES            INGESTA                     NÚCLEO RELACIONAL          CAPA ANALÍTICA
(Kaikki,     →   loaders + recompute    →   (fuente de verdad:    →   (derivada, reconstruible:
 Lexibank,        del objeto propio          form/segment/skeleton      cognados, correspondencias,
 iecor…)          (esqueleto, cripto)        sense/etimología…)         rasgos, polisemia, contacto)
```

- **Fuente primaria:** Kaikki/Wiktextract (Wiktionary, JSONL) — etimología + IPA + sentidos + morfología.
- **Ingesta CLDF** vía `pycldf` (Lexibank, IDS, …) — un solo loader para todo el ecosistema CLDF.
- El **núcleo** es la fuente de verdad; las capas analíticas se **recomputan** desde él (nada se pierde).
- Todo lleva `source_id` (cumplimiento de licencia).

### Familias / subsistemas (replicabilidad)

Todo lo específico de una rama vive en `ingest/families.py`: cada familia declara sus `members`
(lects), `ancestors` (con status), `kaikki_files` y `reconcile_pairs`. Los builders leen la familia
activa por la variable de entorno **`CI_FAMILY`** (default `romance`) y **acotan sus borrados a esa
familia**, de modo que varias familias coexisten sin pisarse.

```bash
CI_FAMILY=romance  ./ingest/build_analytics.sh   # construye todas las capas para Romance
CI_FAMILY=germanic ./ingest/build_analytics.sh   # replica a Germánico (definido, aún sin cargar)
```

Replicar a otra familia = definir su entrada en `families.py`, cargar su Kaikki y correr el orquestador.

---

## Puesta en marcha

Requisitos: **PostgreSQL 18**, **Python 3.12+**.

```bash
# 1) clúster local del proyecto (initdb + puerto 5433 + socket /tmp/ci_pg + carga schema)
./db/setup_dev.sh

# 2) entorno de Python
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Conexión (DSN): `host=/tmp/ci_pg port=5433 user=postgres dbname=corpus_integrativo` (auth local, sin
password). Para pgAdmin: host = `/tmp/ci_pg` (socket) o habilita `listen_addresses='localhost'`.

---

## Correr el pipeline

```bash
PY=.venv/bin/python

# — INGESTA (por familia; ejemplo con las lenguas romances) —
$PY ingest/kaikki_ingest.py Latin Spanish Italian French Portuguese Catalan Romanian …
$PY ingest/cldf_ingest.py    # fuentes CLDF (Lexibank…)

# — DERIVACIÓN del objeto endolingüístico —
./ingest/run_downstream.sh   # segmentar IPA → esqueleto → afijos → core → reconciliar

# — CAPAS ANALÍTICAS (respeta CI_FAMILY) —
./ingest/build_analytics.sh  # cognados, correspondencias, rasgos, polisemia, colex, protoformas, contacto

# — QA (red de seguridad, correr antes/después de cada cambio) —
$PY tests/qa.py
$PY tests/probe_cognates.py  # prueba anti-apofenia: estructura de cognado vs azar
```

Para lenguas ancestro/reconstruidas sin etimología (protos, sabélicas): `kaikki_ingest.py … --all`,
y `skeleton_from_ortho.py` para su esqueleto (romanización ≈ fonémica).

---

## Calidad y garantías

`tests/qa.py` corre ~26 chequeos de regresión (integridad referencial, esqueleto/vocales consistentes,
grafo de etimología, licencia) y **guardarraíles anti-fuga** que verifican por construcción que ninguna
familia contamine a otra. La filosofía es **marcar, no filtrar**: los nombres propios, frases y cores
sospechosos se anotan (`is_proper`, `core_valid`, …) pero se conservan — el corpus crece.

---

## Datos y licencia

Fuentes bajo CC BY / CC BY-SA (Kaikki, LIV², NorthEuraLex, PHOIBLE…). Como la fuente primaria y varias
otras son **CC BY-SA**, la base redistribuible es **CC BY-SA 4.0**; la atribución obligatoria vive en la
tabla `source`. Ver `derechos-datos.md` y `fuentes.md`. Los datos crudos no se versionan (ver
`.gitignore`); se descargan aparte.

---

## Hoja de ruta

Escalar de una familia a **miles de lenguas** de todas las familias: ingesta por lotes vía `pycldf`,
árbol de sub-ramas de Glottolog, prosodia/tono a escala, y revisión del objeto OAS/esqueleto al salir
del indoeuropeo (clicks, implosivas, tonos, retroflejas, morfología no concatenativa). El pipeline ya
está parametrizado por familia; el trabajo de escala es de rendimiento (cargas en bloque, índices) y de
cobertura de fuentes.

## Documentación

`PLAN.md` (diseño vivo), `REPORTE.md` (estado), `ESTRATEGIA-ESCALADO.md` (plan de familias),
`fuentes.md` / `derechos-datos.md` (fuentes y licencias), `ejemplo-*.md` (casos trabajados:
angostura, angst, almohada, lanza, pillow, cabo, afijos).
