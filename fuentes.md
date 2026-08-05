# Fuentes para el Corpus Integrativo — inventario + qué falta

Barrido de fuentes (ago-2026). Dos partes: **(A) lo que YA tenemos** en el repo, y **(B) lo que conviene añadir**,
mapeado a las capas del corpus. Objetivo: no re-bajar lo que existe y saber qué reforzar antes de Fase 0.

---

## A. Lo que YA TENEMOS (en `endolanguage/`)

| Recurso | Ubicación | Tamaño | Qué aporta | Capa |
|---|---|---|---|---|
| **Kaikki (Wiktionary)** | `data/lexicon/kaikki/dict/` | **1.9 GB, 48 lenguas** | **etimologías + IPA + definiciones/sentidos + morfología**, por lengua. Incluye **PROTOS** (Proto‑IE, Proto‑Germánico, Proto‑Itálico, Proto‑Eslavo) y **estadios antiguos** (Old English/French/High German/Norse/Spanish, Gothic) | forma, fonética, morfología, semántica, **genealogía/proto**, etimología |
| **Lexibank** | `data/lexicon/lexibank/` | 350 MB | wordlists densos + cognación LexStat, ~5500 doculectos | forma, cognacy |
| **IE‑CoR (iecor)** | `data/lexicon/iecor/` | 52 MB | cognación **ORO** + estadios atestiguados IE | cognacy, genealogía |
| **IDS** | `data/lexicon/ids/` | 37 MB | ~1300 conceptos, glosas | semántica, forma |
| **NorthEuraLex** | `data/lexicon/northeuralex/` | 13 MB | ~1000 conceptos IPA euroasiáticos | forma, semántica |
| **LIV² (digitalizado)** | `ariadne-lex/data/sources/liv/` (OWL/TTL) | — | **raíces verbales PIE** estructuradas | genealogía/proto, reconstrucción |
| **Grafo etimológico Ariadne** | `ariadne-lex/data/export/` (CLDF: nodes/edges/…) | — | grafo palabra→palabra ya construido + `stats/contact_*` | genealogía, contacto |
| **Nuestros análisis por macrosistema** | `web/data/*.data.js` | 25 archivos | IE, Urálico, Turco, Mongólico, Tungúsico, Dravídico, Afroasiático, Abjaso‑Adigué, Najo‑Daguestánico, Chukotko‑Kamchatka, Esquimo‑Aleutiano, Yukaghir **+** capas: **skeltree (esqueletos)**, conservation, cualic, deltas, deriv, insertions, permcons, ternary, verbs, pairs | **objeto endolingüístico**, esqueletos, macrosistemas |

**Lo grande que no estaba en el radar:** (1) **Kaikki ya trae los PROTO‑formas** (PIE/PGmc/PItal/PSlav) y los estadios
antiguos → gran parte de la capa genealógica/etimológica ya es ingestible. (2) **LIV² digitalizado** → raíces PIE
estructuradas. (3) **web/data ya cubre ~12 macrosistemas** (rango nostrático) con nuestros esqueletos y análisis. (4)
**Ariadne ya es un grafo etimológico CLDF** — plantilla del grafo de linaje.

---

## B. Lo que conviene AÑADIR, por capa

### B1. Genealogía / árbol (¡lo que nos faltó!)
- **Glottolog** — la **clasificación en sub‑ramas** (el `subfamily` que iecor no tenía). Resuelve el problema de
  agrupar a mano. iecor/Lexibank ya referencian glottocodes → enganche directo. **PRIORIDAD ALTA.**
- **Múltiples PIE / reconstrucciones en competencia:** **Pokorny IEW** (digitalizado, indo‑european.info), + Kaikki ya
  agrega de Vaan/Kroonen/Derksen/Beekes con citas. Para la **distribución de probabilidad** sobre variantes.
- **StarLing / Tower of Babel** (Starostin) — Nostrático + bases etimológicas de muchas familias (controvertido →
  **incluir‑con‑fuente**). Para la extensión nostrática y protos alternativos.

### B2. Semántica / polisemia / colexificación (reforzar las redes de sentido)
- **CLICS³** — base de **colexificaciones translingüísticas** (garganta=throat+gorge; estrechez↔angustia). Alimenta
  directo la red de concepto y la colexificación profunda. **PRIORIDAD ALTA.**
- **WordNet (Princeton) + Open Multilingual WordNet + BabelNet** — **synsets, sinónimos, polisemia** estructurada
  (la red polisémica de *cabo*). Kaikki tiene sentidos pero no la red.
- **DatSemShift** (Database of Semantic Shifts, Zalizniak et al.) — **cambios de sentido atestiguados** entre lenguas
  (mejilla→almohada; estrecho→angustia). Alimenta la colexificación profunda y la grammaticalización de afijos.

### B3. Prosodia / acento / tono (la capa difícil — atacarla con fuentes específicas)
- **StressTyp2** — sistemas de **acento de palabra** de ~700 lenguas. La mejor fuente directa de acento.
- **PHOIBLE** — inventarios fonológicos de ~3000 lenguas (incl. **tono**). También base para la normalización y para
  la medida info‑teórica intrínseca (sorpresa dado el inventario).
- **Corpus antiguos CON acento marcado:** Rigveda (védico **acentuado**), griego politónico, lituano, acentología
  balto‑eslava (Derksen/Kortlandt). → acento **para estadios concretos** (justo lo que Verner necesita).

### B4. Fonética / clases de sonido (glue)
- **CLTS** (Cross‑Linguistic Transcription Systems) — normalización IPA + clases de sonido (ecosistema CLDF).
- **PanPhon** — ya lo usamos en código.

### B5. Morfología
- **UniMorph** — paradigmas de **flexión** de ~180 lenguas.
- **Universal Dependencies** — treebanks con morfología + POS (y treebanks **históricos**: latín, gótico, AAA…).
- (Kaikki ya trae parte de la morfología/derivación.)

### B6. Contacto / préstamo / sustrato
- **WOLD** (World Loanword Database) — préstamos + donante + prestabilidad (almohada, sub‑ culto).
- Monografías de **sustrato** por región (celtíbero/ibérico para *lanza*) — bibliográfico, con‑fuente.

### B7. Amplitud (meta: todas las lenguas)
- **ASJP** — listas cortas de **~7000 lenguas** (amplitud casi total; fonética gruesa).
- **Grambank** (~2400 lenguas, rasgos gramaticales) · **WALS** (tipología).
- **Concepticon** — normalización de conceptos (glue del ecosistema CLDF).

### B8. Atestiguación / fechas / frecuencia
- **PROIEL, TITUS, UD‑histórico** — textos de lenguas antiguas (fechas, frecuencia, y **texto acentuado** donde exista).
- **IE‑CoR / Bouckaert** — árboles **fechados** (para `stage.date_lo/hi`).

---

## C. Recomendación para Fase 0 (Latín→Romance denso)
Con lo que YA tenemos alcanza para arrancar el piloto sin bajar casi nada:
- **Formas + etimología + IPA + morfología + protos:** **Kaikki** (Latin, Spanish, Italian, French, Portuguese,
  Catalan, Romanian, Proto‑Italic, PIE) — ya está.
- **Cognación oro / estadios:** iecor.
- **Raíces PIE:** LIV² (Ariadne).
- **Árbol de sub‑ramas:** **Glottolog** (añadir — pequeño).
- **Colexificación/polisemia:** **CLICS³ + un WordNet** (añadir — reforzar las redes de sentido de cabo/angostura).
- **Acento:** de momento el hueco; para latín/romance, marcarlo desde diccionarios/Kaikki donde exista; para védico/
  griego, de corpus acentuados (fase posterior).

**Prioridad de descarga (lo nuevo):** Glottolog › CLICS³ › WordNet/OMW › PHOIBLE › StressTyp2 › DatSemShift › UniMorph
› WOLD › Pokorny › ASJP.

⟨CONFIRMADO⟩ Kaikki = fuente primaria de densidad/etimología/morfología (Fase 0). skeltree se RECOMPUTA limpio.

---

## D. Integración de Lexibank + geografía + comparación con el ecosistema (ago-2026)

**Principio rector (recordatorio de Alejandro):** aunque la carga inicial sea Kaikki, **el corpus es NUESTRO; las
fuentes son solo ALIMENTADORES.** El modelo no privilegia ninguna fuente: todo entra a nuestro esquema normalizado,
se recomputa (esqueleto/cripto) y lleva `source_id`. La identidad del corpus = nuestras capas (esqueleto, objeto
criptológico, genealogía probabilística, las 4 redes), que ninguna fuente provee.

### D1. Cómo integramos Lexibank (y sus ~100 sub-datasets)
Lexibank es **UN CLDF agregado** con columna `Dataset` que separa los ~100 componentes. Mapeo a nuestro esquema:
- `languages.csv` → **`lect`**: trae `Glottocode, Family, Subgroup, Macroarea, Latitude, Longitude, Dataset` +
  flags de subconjunto curado `LexiCore/ClicsCore/CogCore/ProtoCore/Selexion`. Cada `Dataset` = una fila `source`
  (con SU licencia — ⚠️ los componentes de Lexibank tienen licencias distintas: verificar per-dataset).
- `forms.csv` → **`form`+`segment`**: `Segments` (IPA), `Loan`→`is_loan`, `Cognacy`→`cognate_set`/`member`
  (¡la cognación VARÍA por dataset — unos oro, otros LexStat — se etiqueta con procedencia!). Trae ya features
  computados (CV_Template, Prosodic_String, Dolgo/SCA classes) que podemos ingerir o recomputar.
- `concepts.csv` → **`concept`** (con `Concepticon_ID` → enganche directo a nuestro backbone Concepticon).
- **Estrategia:** ingerir por dataset, con `source` por componente; usar los flags core (LexiCore/ClicsCore) para
  elegir el slice; reconciliar lenguas por **Glottocode** (no por nombre) contra `lect`/Glottolog.

### D2. Geografía (sí, la queremos)
`lect` ahora tiene **`macroarea, latitude, longitude`** (+ `family, subgroup, glottocode`). Fuente: Lexibank/
Glottolog. Alimenta la **hipótesis de geografía del cambio** (ciudad/ruta rápido vs isla/montaña lento) y permite
mapas/atlas. Nota: `macroarea` (GEOGRÁFICO: Eurasia/África…) ≠ `macrosystem` (GENEALÓGICO: indo-europeo/semítico…).

### D3. Tu lista vs la nuestra — estado (HAVE / PLANNED / NUEVO)
- **Núcleo del ecosistema:** Lexibank ✅have · Concepticon ✅have · CLDF (estándar, lo adoptamos) · Glottolog ⏳planned
  · CLTS ⏳planned.
- **Léxicas:** ASJP ⏳ · IDS ✅ · NorthEuraLex ✅ · WOLD ⏳ · **ABVD 🆕** (austronesio, fase multi-familia) ·
  **STEDT 🆕** (sino-tibetano) · **Reflex 🆕** (África).
- **Fonológicas:** PHOIBLE ⏳ · CLTS ⏳ · **Phonobank 🆕 ¡ALTA relevancia!** (cambios de sonido, **correspondencias**,
  **alineamientos** — es *justo* nuestro objeto de transformations; a explorar apenas salga/esté disponible).
- **Tipológicas:** Grambank ⏳ · WALS ⏳ · **AUTOTYP 🆕** · **SAILS 🆕** (Sudamérica).
- **Semánticas:** Concepticon ✅ · CLICS ⏳ · **NoRaRe 🆕** (normas psicolingüísticas: frecuencia, iconicidad,
  concreción — relevante a la psicofonología/endolingüística y para PONDERAR).
- **Numerales:** **Numeralbank 🆕**. **Paradigmas:** **Parabank 🆕** (flexión — mejor integrado en CLDF que UniMorph).
- **Filogenia:** Glottolog ⏳ · **Glottobank 🆕** = el consorcio paraguas (Lexibank+Grambank+Numeralbank+Phonobank+
  Parabank, todos interoperables por CLDF+Glottolog+Concepticon).
- **Herramientas (adoptar para la INGESTA):** **LingPy** (ya lo usamos) · **pycldf, pyconcepticon, pyglottolog,
  pyclts, cldfbench** — leer CLDF nativamente en vez de parsear a mano.
- **Corpus textuales (UD/OPUS/OSCAR…):** fuera de alcance por ahora (somos léxico/etimológico); **UD** útil solo para
  morfología y treebanks históricos (acento/atestiguación).

### D4. El apalancamiento clave (CLDF)
Como Lexibank, Grambank, Phonobank, Numeralbank, Parabank, WALS, WOLD, CLICS, ASJP **comparten CLDF + Glottolog +
Concepticon + CLTS**, si construimos la ingesta sobre **pycldf**, TODOS entran con **un solo loader** y se reconcilian
por Glottocode + Concepticon_ID. Ese es el multiplicador: adoptar el estándar CLDF como puerta de entrada, y nuestro
esquema propio (con esqueleto/cripto/genealogía-probabilística) como el destino que ninguna fuente tiene.

⟨ABIERTO⟩ ¿priorizamos **Phonobank** (correspondencias/alineamientos, muy nuestro) en cuanto lo tengamos? ¿ingesta
vía **pycldf** (loader único CLDF) como arquitectura de entrada?
