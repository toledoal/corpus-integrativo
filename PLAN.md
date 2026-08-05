# Corpus Integrativo — Plan (v0.3, documento vivo)

**Estado:** borrador iterando. **v0.3 consolida 5 entradas trabajadas** (angostura, Angst, almohada, lanza, pillow)
sobre v0.2 (que integró `idea.md`). Secciones con **⟨ABIERTO⟩** esperan tu decisión. Arranque: 2026-08-04.

**Ejemplos que validan el diseño** (`ejemplo-*.md`): *angostura* (herencia, esqueleto **conservado**), *Angst*
(cognado entre ramas, esqueleto **por‑estadio**, colexificación profunda), *almohada* (préstamo **inter‑macrosistema**,
raíz‑y‑patrón), *lanza* (**sustrato dudoso**, esqueleto **mutado**, cognación condicional), *pillow* (préstamo
**intra‑macrosistema**, enlace por **concepto**), *cabo* (**polisemia ≥4**, lenición, código‑vs‑segmento),
*sub‑/‑less* (**afijos** como entradas‑morfema).

**Norte del proyecto (de idea.md).** Al mirar **una** entrada del corpus queremos ver **toda la historia de la
palabra**: su forma, su sonido, su sentido, y su linaje completo hacia atrás —con sus dudas, sus fuentes y sus
probabilidades— hasta el proto y más allá. Ambicioso a propósito: la meta última es **todas las lenguas humanas**. No
se termina hoy; se empieza bien.

**Por qué existe.** Los muros de esta sesión —celdas vacías, artefactos de transcripción, pseudorreplicación,
genealogía inventada a mano— no eran fallos del método sino del corpus. Este es el corpus que el método necesita.

---

## 0. Principios de diseño

1. **La genealogía está EN el dato, y esta vez NO peleamos con ella: nos adaptamos.** Si hay discrepancia entre
   formas (p.ej. varias reconstrucciones de PIE), se **integran con probabilidad**, no se elige una. La genealogía es
   **flexible pero exhaustiva** y **siempre con fuente académica**. *(idea.md §1)*
2. **La "duda" es un estado de primera clase.** Si no hay atestiguación pero hay sospecha (p.ej. sustrato de *lanza*),
   se registra COMO duda, con su probabilidad y su fuente/argumento — no se borra ni se afirma. *(idea.md §1)*
3. **Transcripción en capas y normalizada** (IPA cruda + fonémica normalizada + diacríticos alofónicos explícitos).
   *(mata el artefacto ʲ de hoy)*
4. **Densidad, no Swadesh** — vocabulario básico y extendido; muchas formas por lengua.
5. **El entorno se conserva** — acento/prosodia, vocales, sílaba, frontera morfológica: los disparadores de las leyes.
6. **Cognación ≠ polisemia.** Dos redes distintas: cognados/coderivados (historia de la FORMA, entre lenguas) y
   sinónimos/polisemia (red del SENTIDO, dentro de la lengua). Los sinónimos **no** necesitan ser cognados para
   conectarse. *(idea.md §5)*
7. **Metadatos de exchangeabilidad** (conjunto cognado, lengua, rama) → nulos correctos por diseño.
8. **Procedencia total y reproducibilidad.** Cada dato y cada afirmación genealógica apunta a su **fuente**; nada
   imputado en silencio. La fuente académica es lo fundamental en la capa histórica. *(idea.md §1)*
9. **Extensibilidad hacia atrás y hacia los lados.** El linaje debe poder crecer a nostrático u otras
   macroconstrucciones si se descubren o si las integramos nosotros. *(idea.md §3)*

⟨ABIERTO⟩ ¿reordenas o añades principios?

---

## 1. Qué ES

Una base de datos **multi-capa, multi-estadio y multi-fuente** que, por cada ítem léxico a través de lenguas y
épocas, une:

- **Forma** — segmentos IPA (crudos + normalizados), ortografía.
- **Fonética/fonología** — rasgos, inventario, sílaba, **acento/prosodia**, tono, cantidad; **análisis vocálico**.
- **Morfología** — segmentación, raíz, afijos, categoría.
- **Semántica** — concepto, glosa multilingüe, sentidos **en contexto**, y una **red polisémica** por lengua.
- **Genealogía** (§3) — linaje probabilístico y exhaustivo con fuentes, hasta proto(s) y más allá.
- **Contacto/sustrato** — préstamos y sustratos por probabilidad, incluso dudosos.
- **Análisis derivado** — fonético, vocálico, y **criptológico** (la palabra como objeto matemático, montado sobre el
  **esqueleto consonántico**): operadores Δ/T, kernels K, medidas info-teóricas. *(OAS aplazado, §6e.)*

**Cuatro redes de relación** conviven sobre las mismas entradas (validadas por los 5 ejemplos):
1. **Cognacy — red de la FORMA** (genealógica, entre lenguas/tiempo: cognados, protos, sustratos). *(angostura, Angst)*
2. **Polisemia — red del SENTIDO intra‑lengua** (sinónimos/acepciones NO‑cognados, colexificación). *(todas)*
3. **Concepto — red del SENTIDO entre lenguas** (traducciones vía el nodo Concepticon, aun sin cognación).
   *(almohada↔pillow: mismo concepto PILLOW, no cognados)*
4. **Cohorte de contacto — red del PRÉSTAMO** (agrupación por patrón de préstamo; ni cognados ni sinónimos).
   *(arabismos con al‑)*

Sobre ellas corre la **capa analítica de correspondencias/cifrado** (operadores Δ/T como aristas, códigos, kernels):
no es una "relación" social sino la firma matemática derivada (§6).

⟨ABIERTO⟩ nombre propio del corpus; ¿piloto IE o multi-macrosistema desde el día 1? (la meta es todas las lenguas).

---

## 2. Cómo FUNCIONA (arquitectura)

```
  FUENTES  →  INGESTA/NORMALIZACIÓN  →  NÚCLEO RELACIONAL+GRAFO  →  CAPA ANALÍTICA  →  VISTAS/APPS
 (CLDF,       (IPA→segmentos,          (lects, linaje probab.,     (operadores,       ("historia de la
  Kaikki,      normalización            formas, cognados,           kernels, códigos,  palabra", atlas,
  dicts,       fonémica, dedup,         sentidos, polisemia,        crypto, MDL,       papers)
  reconstr.)   fuentes)                 correspondencias)           nulos por rama)
```

**Fuente de verdad = núcleo relacional + grafo de linaje.** Todo lo derivado (operadores, códigos, medidas
criptológicas, redes) se **recomputa** del núcleo; nunca se edita a mano. La escala "todas las lenguas" obliga a
elegir bien tecnología y arquitectura desde el principio (idea.md §4).

**Estándar de interoperabilidad:** ingerir **CLDF** (Concepticon, Glottolog, CLTS, panphon) pero con **esquema
propio** más rico —CLDF no modela linaje probabilístico, prosodia, morfología, polisemia ni códigos como los
necesitamos.

⟨ABIERTO⟩ tecnología y arquitectura (ver §5) — decisión temprana e importante por la escala.

---

## 3. GENEALOGÍA — el corazón (reescrito con idea.md)

Esta vez la genealogía se **incluye y se abraza**. No un árbol único y oficial, sino un **grafo probabilístico,
multi-padre, multi-fuente y exhaustivo**.

### 3a. La escalera de niveles (cada forma vive en un "lect" tipado)
Del más fino al más profundo:

```
 idiolecto → dialecto → lengua → subsistema/subfamilia (p.ej. itálico)
          → lengua-madre derivada (latín vulgar) → lengua anterior (latín)
          → proto-rama (proto-itálico) → PROTO-INDOEUROPEO (plural, ver 3c)
          → [futuro] nostrático / macroconstrucciones
```
Cada nivel es un tipo de nodo `lect`; una entrada puede anclarse a cualquier nivel y **subir** por el grafo.

### 3b. El grafo de linaje (no un árbol)
Aristas `ancestry_edge(hijo → padre)` con:
- **kind** ∈ {herencia, sustrato, préstamo, reconstruido-de}
- **probabilidad** (peso; permite integrar discrepancias en vez de elegir una) *(idea.md §1)*
- **status** ∈ {atestiguado, reconstruido, **dudoso**}  *(la duda es dato, no ausencia)*
- **fuente** (cita académica — obligatoria en la capa histórica)

Un mismo ítem puede tener **varios padres** (herencia + sustrato + préstamo), cada uno con su probabilidad. Ejemplo
*lanza*: herencia latina (prob alta) **+** sustrato celtíbero/ibero (status=dudoso, prob media, con fuente/argumento).

### 3c. PIE plural (la "madurez nueva" que pides) *(idea.md §1)*
El proto-indoeuropeo **no es un punto**: hay modelos y temporalidades dialectales distintas (p.ej. hipótesis
Indo-Anatolia / PIE tardío vs. temprano, reconstrucciones de distintas escuelas). Los modelamos como **nodos/
hipótesis PIE en competencia**, cada uno con:
- su forma reconstruida, su modelo/escuela, su cercanía relativa (p.ej. "más cercano al anatolio"), y su **fuente**.
Integrar diversas fuentes de PIE (y de otros protos) **no será fácil** — se acepta como trabajo necesario; lo
fundamental es **saber y guardar la fuente académica** de cada variante.

### 3d. Sustratos por probabilidad
Sustratos principales como contribuyentes ponderados (celtíbero, ibero, griego, púnico… en romance; y los que
correspondan en cada zona), incluso sin atestiguación → status=dudoso + fuente.

### 3e. Extensible a nostrático y más *(idea.md §3)*
El grafo no se corta en PIE: nodos y aristas hacia macroconstrucciones (nostrático u otras) se añaden si se descubren
o si las proponemos nosotros — siempre con probabilidad y fuente.

### 3f. La vista "toda la historia de la palabra" *(norte, idea.md §2)*
Consulta estrella: dada una forma, recorrer el grafo hacia arriba y devolver el **linaje completo** —cada estadio,
cada proto en competencia con su probabilidad, cada sustrato, cada duda, cada fuente— renderizado legible.

**DECIDIDO (Alejandro):**
- **Reconstrucciones en conflicto → anotar AMBAS (todas) y derivar una probabilidad por DISTRIBUCIÓN**, y marcarla.
  Es decir, cada variante se guarda como hipótesis; la probabilidad sale de la distribución sobre las variantes
  (ponderada por respaldo/citación), no de elegir una a mano. Se muestra la variante marcada + la distribución.
- **Fuentes de proto → tomar las MÁS CITADAS, pero SIN dar prioridad a una sola.** Varias fuentes ponderadas por
  citación; ninguna es "la oficial". (LIV, de Vaan, Kroonen, Pokorny, Ringe… entran todas como fuentes ponderadas.)

⟨ABIERTO⟩ métrica exacta de "respaldo/citación" para la distribución (¿nº de fuentes que la sostienen, peso por
autoridad de la fuente, ambos?).

---

## 4. Qué DATOS / fuentes

| Fuente | Aporta |
|---|---|
| **iecor** | cognación oro, estadios atestiguados |
| **Lexibank** | densidad (Latín 1032, Rumano 2266… 1.74M formas) |
| **IDS / NorthEuraLex** | amplitud semántica (~1000-1300 conceptos) |
| **Kaikki/Wiktionary** | etimologías + IPA + morfología + **polisemia**, enorme |
| **Diccionarios etimológicos / reconstrucción** (LIV, de Vaan, Kroonen, Pokorny, Ringe…) | **múltiples PIE y protos con fuente** |
| **WOLD + literatura de sustrato** | préstamos y sustratos (incl. dudosos) |
| **Fuentes de acento/prosodia** | diccionarios con acento (los wordlists no lo traen) |
| **Datos endolingüísticos propios** | códigos OAS, glosas NEL, conservación/pérdida |

**Fusión multi-fuente:** guardar **todas** las cognaciones/reconstrucciones con procedencia; resolver por reglas
explícitas + probabilidad, nunca promediando en silencio.

**PROSODIA / ACENTO / TONO — problema difícil, aceptado y aplazado (Alejandro).** No hay fuente evidente; pueden ser
diccionarios u otras fuentes, y **no se conseguirá de inmediato**. Complicación extra: en notación IPA, **el acento
de una lengua puede diferir muchísimo de otro de la misma lengua** — así que capturar "el acento" no es leer un
símbolo. Aun así **tenemos que poder identificar el acento de alguna forma**. Diseño: dejar el **slot** en el esquema
(campos `stress`/`tone`/prosodia en `segment`/`form`) preparado, poblarlo cuando haya fuente, y tratar la
identificación del acento como una subtarea de investigación aparte. **De esta capa cuelga el endorritmo** (§6): sin
acento/prosodia no hay endorritmo, así que ambos se aplazan juntos.

⟨ABIERTO⟩ (investigación futura) cómo identificar/normalizar el acento entre variedades; qué fuentes de acento existen.
¿qué diccionarios etimológicos/reconstrucción priorizar (todos los más citados, sin una sola prioritaria)?

---

## 5. Base de DATOS (tecnología y esquema)

**DECIDIDO (Alejandro): PostgreSQL** — BD grande y madura, con capacidad de nodos/grafos. El linaje (grafo §3) se
resuelve con consultas recursivas (recursive CTE) y/o la extensión de grafos **Apache AGE** dentro del mismo Postgres
(un solo sistema, sin sincronizar dos BDs). Objetos matemáticos → tablas + materialización a matrices/tensores
(numpy/scipy) en la capa analítica. La escala "todas las lenguas" confirma la elección.

**Esbozo de esquema (v0.3 — consolidado con los 5 ejemplos):**
- `lect(id, name, level, glottocode?, macrosystem, date_lo, date_hi, attested?)` — level ∈ {idiolecto, dialecto,
  lengua, subfamilia, proto‑rama, PIE, nostrático}. `macrosystem` es del lect; el macrosistema de ORIGEN de un
  préstamo vive en la arista, no aquí *(almohada: lect=IE, origen=semítico)*.
- `ancestry_edge(child, parent, kind, law_class, probability, status, crosses_macrosystem, source_id)` — grafo
  probabilístico (§3b). `kind` ∈ {herencia, préstamo, sustrato, reconstruido}; `law_class` ∈ {Grimm, satem,
  palatalización… (herencia) | adaptación (préstamo)}; `status` ∈ {atestiguado, reconstruido, **dudoso**};
  `crosses_macrosystem` (almohada=sí, pillow=no).
- `protoform_hypothesis(etymon_id, lect_id, form, model, prob, source_id)` — **PIE plural** (§3c); `prob` por
  DISTRIBUCIÓN sobre variantes (las más citadas, sin priorizar una).
- `form(id, lect_id, concept_id, ipa_raw, segments_raw, segments_norm, orthography, stress, source_id, is_loan)`
- `segment(form_id, pos, ipa, phoneme_norm, syllable, role, stress, length, tone)` · `feature(phoneme, feat, value)`
- `morph(form_id, span, role=root/affix/**pattern**, gloss)` — soporta concatenativo **y raíz‑y‑patrón** (semítico,
  almohada); es **por‑estadio** (al‑/mi‑ segmentables en árabe, opacos en español).
- `cognate_set(id, source, confidence, deep_colex?)` · `cognate_member(set_id, form_id, **condition_hyp_id?**)` —
  **red de la FORMA**; `condition_hyp_id` = **cognación CONDICIONAL** a una hipótesis del grafo de duda *(lanza)*;
  `deep_colex` = colexificación profunda a nivel de raíz *(estrechez↔angustia)*.
- `sense(id, form_id, gloss_en, gloss_de, context)` · `polyseme_link(sense_a, sense_b, lect_id, relation)` —
  **red del SENTIDO intra‑lengua** (NO requiere cognación). `colex(concept_a, concept_b, lect_id)` — colexificación.
- `concept(id, concepticon_id, gloss)` + `form.concept_id` → **red del SENTIDO entre lenguas**: el nodo de concepto
  une traducciones NO cognadas *(almohada↔pillow, ambas PILLOW)*.
- `contact_cohort(id, pattern, note)` · `cohort_member(cohort_id, form_id)` — **red del PRÉSTAMO** *(arabismos con al‑)*.
- `substrate_edge(form_id, source_lect, probability, status, source_id)` — sustratos por probabilidad; multi‑hipótesis
  con `status=dudoso` *(lanza: celtíbero/ibérico/herencia, cada una con prob+fuente)*.
- `skeleton(id, form_id, **stage_lect_id**, cons_skeleton, core_skeleton, code, **skeleton_lineage_id**)` — esqueleto
  consonántico (palabra + núcleo, SIN afijos), **por‑ESTADIO** *(Angst: /g/ en AAA, ∅ en moderno)*;
  `skeleton_lineage_id` agrupa un mismo código a través de estadios y **ramas** (resonancia estructural:
  Ξ·Χ·Σ·Θ en itálico Y germánico); doble esqueleto = palabra fósil + raíz donante *(almohada)*.
- `correspondence(from_lect, to_lect, a, b, env, count, **corr_type**, law_class, crosses_macrosystem)` — derivada;
  `corr_type` ∈ {**conservar** (angostura), **mutar** (lanza, palatalización), **truncar** (pillow, almohada)}.
- `crypto(form_id, skeleton_id, feature_vectors, self_info, …)` — **montado sobre el esqueleto** (§6a).
- `source(id, citation, url, kind, license, redistributable)` — **fuentes académicas** (obligatorio; `license` +
  `redistributable` para cumplimiento CC y **cuarentena** de fuentes NC/ND — ver `derechos-datos.md`).

*(Nota: no hay tabla OAS — OAS requiere interpretación psicodinámica y aún no aplica; ver §6.)*

⟨ABIERTO⟩ versionado del corpus (dvc/dolt/git-lfs). *(Postgres ya decidido; grafo dentro de Postgres vía AGE/CTE.)*

---

## 6. OBJETOS que el corpus soporta

### 6a. Criptológico — la palabra como objeto matemático *(idea.md)*
Cada forma tiene una **firma matemática montada sobre su ESQUELETO CONSONÁNTICO** (§6e): su vector en F₂ⁿ de rasgos,
sus operadores Δ (simétrico) y T (dirigido), su comportamiento bajo los kernels de correspondencia K_{A→B} (canal
estocástico) y medidas info-teóricas (entropía, equivocación, unicity). Es la capa que trata cada palabra como texto
cifrado y el conjunto como un sistema de cifrado — el puente al programa transformations. **No incluye OAS por ahora**
(§6e).

### 6b. Análisis vocálico y fonético
Inventario, rasgos, sílaba, acento, tono, cantidad; frecuencias y distribuciones vocálicas; el entorno que condiciona
las leyes.

### 6c. Las CUATRO redes de relación *(consolidado de los 5 ejemplos)*
Una entrada participa en cuatro redes ortogonales; el esquema (§5) las modela por separado:
1. **Cognacy (forma):** cognados/coderivados entre lenguas; puede ser **condicional** a una hipótesis del grafo de
   duda *(lanza)*. Incluye **colexificación profunda** a nivel de raíz *(estrechez↔angustia, \*h₂enǵʰ‑)*.
2. **Polisemia (sentido, intra‑lengua):** sinónimos/acepciones en contexto, **aunque NO sean cognados** → red
   polisemántica por lengua.
3. **Concepto (sentido, entre lenguas):** el nodo Concepticon une traducciones **no cognadas** *(almohada↔pillow)*.
4. **Cohorte de contacto (préstamo):** agrupación por patrón de préstamo *(arabismos con al‑)* — ni cognados ni
   sinónimos.
Nota: un enlace puede vivir en **dos** redes a la vez *(Angst↔angustia = cognados Y sinónimos)*.

### 6d. Matemáticos (transformations) y lingüísticos/históricos
F₂ⁿ, Δ/T, σ:T→Δ, kernel K, XOR/combinatoria aditiva, S_k (metátesis), MDL, unicity, nulos por rama; segmento/fonema/
sílaba/morfema/concepto/cognado/linaje/estadio/protoforma(s)/sustrato.

### 6e. Objeto ENDOLINGÜÍSTICO — por ahora, SOLO el esqueleto consonántico *(DECIDIDO, Alejandro)*
De momento el único objeto endolingüístico de primera clase es el **esqueleto consonántico de la palabra y de su
núcleo/raíz** — **sin** prefijos, sufijos, afijos, terminaciones ni desinencias — **conectado por un ID** (tabla
`skeleton`, §5). Ya existe maquinaria base para construirlo (`src/build_skeltree.py`, `src/gi/skeletons.py`,
`src/cc/skeletons.py`) que hay que integrar al corpus.

**Aplazados explícitamente:**
- **OAS** — requiere interpretación psicodinámica; aún no llegamos a esa etapa. No entra ahora.
- **Endorritmo** — su única liga posible es vía **acento y prosodia** (§4), aplazados por falta de fuente; se integra
  cuando esa capa exista.
- Macrosistemas, inversión cuálica, 4 niveles del endolenguaje — más adelante.

### 6f. CÓMO se incluye el objeto criptológico en CADA entrada *(la decisión de modelado clave)*
El objeto criptológico tiene **tres aridades**, y no todo vive dentro de la fila de la palabra. Ese fue el error de
los pipelines viejos (todo suelto). En el corpus:

| Aridad | Qué es | Dónde vive |
|---|---|---|
| **Monádica** (1 forma) | esqueleto consonántico + **código canónico** + vectores F₂ⁿ de sus segmentos + medida info-teórica intrínseca | **en la entrada** (tablas `skeleton`, `crypto` con `form_id`) |
| **Diádica** (2 formas) | operador Δ(a,b) simétrico y T(a→b\|entorno) dirigido | **arista** entre dos entradas cognadas / entre entrada y su ancestro (tabla `correspondence` como edge, o `operator_edge`) |
| **Sistémica** (conjunto) | kernel K_{A→B}, C(O), unicity | **referenciada** desde el `lect` / par de lects; no se duplica por palabra |

**Por entrada (monádico), derivado y recomputable desde los segmentos** — nunca a mano; ancla = `skeleton_id`:
1. `skeleton` — esqueleto consonántico (palabra + núcleo, sin afijos) + **código canónico** (consonantes por valor
   cualo normalizado; maquinaria base: build_skeltree/gi/cc).
2. `crypto(form_id, skeleton_id, feature_vectors, self_info, …)` — la firma matemática de esa forma.

**Entre entradas (diádico):** Δ/T **no** se guardan en la fila; son **aristas** que unen dos entradas del mismo
conjunto cognado o una entrada con su ancestro en el grafo de linaje (§3). Desde una entrada se consulta: "mis
operadores con mis cognados" y "el operador dirigido de mi ancestro→yo".

**Hacia el sistema (sistémico):** la entrada apunta a su `lect`; el par `lect→ancestro` posee el kernel K, C(O), etc.

**El pago histórico:** como el linaje es un grafo, subir desde una entrada devuelve la **cadena de operadores
dirigidos** estadio a estadio — los "pasos de cifrado" del esqueleto del ancestro al de la palabra. Eso alimenta la
vista "toda la historia de la palabra" (§3f).

**Ejemplo — latín *centum*:** monádico → esqueleto `k·n·t·m`, núcleo `k·n·t`, código `Χ·Ξ·Θ(·Ϻ)`, rasgos por
segmento. Diádico → arista a esp. *ciento* `k→θ/s | _V[frontal]`, a fr. *cent* `k→s`. Sistémico → apunta a
K_{latín→español}. "Historia de *centum*" = subir el grafo y leer esa secuencia de operadores hasta proto-itálico y
PIE (plural).

**DECIDIDO (Alejandro): el código canónico de la PALABRA va en SÍMBOLOS de clase (Χ Ξ Θ Ϻ Σ Λ Φ…); el NÚCLEO/raíz
va en LETRAS consonánticas.** Cada entrada guarda ambos: `code` (símbolos, palabra) y `core_skeleton` (letras, raíz).
*(ej.: cabo → código Χ·Φ, núcleo k·b).*

⟨ABIERTO⟩ ¿guardamos la medida info‑teórica intrínseca por entrada desde Fase 0 o después?

### 6g. Tres tipos de correspondencia de ESQUELETO *(clave, de los 5 ejemplos)*
Al comparar el esqueleto de una entrada con el de su ancestro/cognado, la correspondencia (`corr_type`) es de tres
clases — y **la clase es el hallazgo**:
- **CONSERVAR** — el esqueleto se mantiene (Δ=∅ en las consonantes). *angostura* (Ξ·Χ·Σ·Θ lat→esp) y *Angst* (Ξ·Χ·Σ·Θ
  itálico↔germánico). El invariante que perseguimos; consultable vía `skeleton_lineage_id`.
- **MUTAR** — una consonante cambia de clase por una ley. *lanza*: Χ(k)→Θ(θ) por palatalización ante vocal frontal
  (la misma ley k→θ recuperada en los papers). La mutación **ES** la ley de sonido.
- **TRUNCAR** — el esqueleto pierde/gana posiciones. *pillow*: Φ·Λ·v·Ξ (pulvīnus) → Φ·Λ (reducción de préstamo).

Dos ejes cruzan esto: **herencia vs préstamo** (`law_class`) y **por‑estadio** (comparar estadios comparables, no
superficies modernas: el /g/ de *Angst*, la /h/ de *almohada*).

**`corr_type` tiene NIVEL** *(de cabo):* la lenición p→b **conserva la clase‑código** (p,b ∈ Φ) pero **muta el
segmento**. Se guardan ambos niveles — el esqueleto puede conservarse en símbolos y mutar en letras.

### 6h. AFIJOS y morfemas ligados — entradas de primera clase *(de sub‑, ‑less)*
Un afijo **no** entra en el esqueleto‑CORE (se elimina), pero **sí es una entrada‑morfema** con: su **lineage** propio
(sub‑ < lat *sub* < PIE \*upo; ‑less < AI ‑lēas < PGmc \*lausaz, cognado de al. ‑los y de *loose/lose*), su
**sentido/función + grammaticalización** (\*lausaz 'suelto' → ‑less 'sin'), su **esqueleto propio** (sub‑ = Σ·Φ /
s·b; ‑less = Λ·Σ / l·s), y su **productividad**. Se enlaza a las palabras por `morph`; el esqueleto‑PALABRA lo
incluye, el CORE no *(igual que al‑/mi‑ en almohada)*. Añade dos relaciones: **composición semántica** (base+afijo:
fear+‑less='sin miedo') y **cohorte morfológica** (todas las palabras con ‑less), hermana de la cohorte de contacto.

**Polisemia ≠ homonimia** *(de cabo):* varios `sense` de una `form` que comparten étimo = **polisemia** (radial:
cabo); misma forma con étimos distintos = **homonimia** (ingl. *bank* río vs *bank* dinero). La diferencia vive en si
los sentidos comparten `cognate_set` → flag a marcar.

⟨ABIERTO⟩ ¿afijos en `morph` con flag `is_bound`, o tabla `affix` propia con su lineage y skeleton?

---

## 7. Qué DESBLOQUEA
- Leyes condicionadas con potencia (densidad + entorno + cognación oro).
- Leyes prosódicas (Verner…) — por fin hay acento.
- Frontera de recuperabilidad demostrada — estadios atestiguados densos con fecha.
- **"Toda la historia de la palabra"** — la vista de linaje probabilístico con fuentes.
- **Red polisémica por lengua** y resonancias de sentido.
- Análisis criptológico sobre el esqueleto consonántico (OAS más adelante).
- Nulos honestos por diseño (exchangeabilidad en el esquema).

---

## 8. Fases (sin morir en lo titánico; la meta es todas las lenguas, no hoy)
- **Fase 0 — Piloto de un linaje limpio y PROFUNDO.** Latín→Romance denso, TODAS las capas (forma, acento,
  morfología, sentido+polisemia, cognación oro, sustratos con duda, linaje probabilístico con fuentes hasta
  proto-itálico y PIE plural). Prueba del esquema completo en pequeño.
- **Fase 1 — Más ramas con genealogía real** (Glottolog + protos múltiples): germánico, eslavo, indoario, iranio…
- **Fase 2 — Prosodia y morfología a escala** (la capa que nadie más tiene).
- **Fase 3 — Multi-macrosistema, códigos OAS, polisemia global, extensión nostrática.**
- **Horizonte — todas las lenguas humanas.**

⟨ABIERTO⟩ ¿Latín→Romance como Fase 0? ¿o un linaje donde el sustrato/PIE-plural luzca más (p.ej. castellano con
celtíbero/ibero, tu ejemplo *lanza*)?

---

## 9. Preguntas abiertas grandes
1. Nombre y alcance inicial (IE vs multi-macrosistema).
2. ~~Tecnología~~ **DECIDIDO: PostgreSQL** (grafo dentro vía AGE/CTE). Pendiente solo: versionado del corpus.
3. Fuente primaria de densidad+morfología+etimología (¿Kaikki?) y **fuentes de PIE/protos** a priorizar.
4. Cómo integrar probabilidad cuando hay reconstrucciones en conflicto.
5. De dónde sale el **acento/prosodia**.
6. ~~Objetos endolingüísticos~~ **DECIDIDO: solo el esqueleto consonántico (palabra + núcleo, sin afijos) con ID**;
   OAS/endorritmo/macrosistemas aplazados (§6e).
7. Política de fuentes: formato de cita, nivel de exigencia por tipo de afirmación.

---

*(Documento vivo. v0.2 integró idea.md; Alejandro revisa y sigue dictando.)*
