# Log de curación del corpus

*Rastro versionado de cada decisión de curación. Meta: un corpus **curado, reproducible y honesto sobre sus
huecos** — no solo funcionando. Cada cambio del inventario IPA→clase o de las reglas de ingesta se registra aquí
antes de usarse (protocolo C0: revisión versionada). El git-log tiene el detalle mecánico; esto tiene el porqué.*

---

## 1. Inventario IPA→clase OAS (revisiones versionadas)

**Base (v0).** `P→Φ T→Θ K→Χ S→Σ L→Λ M→Ϻ N→Ξ`. Fricativas por lugar (f→Φ, θ→Θ, x→Χ); S = solo sibilantes.
Normalización canónica del esqueleto (róticas→r, dorsales→x/h, nasales→n/m). Vocales conservadas; el esqueleto
sale del **IPA** (independiente del script).

Ampliaciones al ir cargando familias (cada una motivada por símbolos IPA reales, cazados por el QA `SKEL·'?'`):

| v | Familia que lo trajo | Cambio | Motivo |
|---|---|---|---|
| v1 | Germánico | vocales ʏ ɶ ɞ ᵻ ᵿ → VOW | vocales redondeadas ant./centrales |
| v1 | Germánico | ʍ→Φ, ɧ→Χ, ɬ ɮ ǁ ɺ→Λ | consonantes germánicas/laterales |
| v1 | Germánico | tono superíndice ¹²³⁴⁵±, entonación ↗↘, clicks prosódicos → IGNORE (marca 'T') | notación, no segmento |
| v2 | Eslavo | þ→Θ (thorn); yers ъ ь + nasales ǫ ę ě ą → VOW; ⁽⁾ (palatalización opcional) → IGNORE | reconstrucción/ortografía eslava |
| v3 | Indo-iranio | ◌ (ancla devanagari) → IGNORE | notación devanagari |
| v4 | Céltico | ɰ (aprox. velar) → GLI; ɯ (vocal posterior) → VOW | fonología celta |
| v5 | Índico | `normalize._DEV` devanagari ampliado: vocales independientes अआइउए…, retroflejas ठढणञङ, nukta क़ज़ड़… | esqueleto ortográfico de Sánscrito/Pali/Prácrito en devanagari |

**Africadas (v2).** tʃ dʒ ts dz → **Σ** (por destino, transición Θ→Σ). Corrige un bug previo: la africada con
tie-bar (t͡ʃ) se clasificaba como Θ por su primer carácter.

**Regla BICLASE — implementada, MEDIDA y REVERTIDA (v-experimental, apagada por default).** El documento
`oas-segmentos-biclase` propone ʃʒʂʐɕʑ→Σ·Χ, ɳɲŋɴ→Ξ·Χ, ʎ→Λ·Χ. Se implementó (con guarda de asimilación: ŋ+velar =
/n/ asimilada, no dobla Χ) y se **midió** su efecto sobre la conservación de código entre coderivados
(`analysis/biclass_conservation.py`): **reduce la conservación en las 4 familias medidas** → falsa la predicción §6
a nivel corpus. **Decisión de Alejandro: revertida a `biclass=False`.** Se conserva la maquinaria + flag + medidor
para una versión futura **condicionada a la genealogía** (aplicarla solo donde el etymon evidencia racimo dorsal —
la ambigüedad del `š` de superficie se resuelve en la protoforma). Ver `docs/experimento-biclase.md`.

## 2. Normalización de datos (multi-fuente, multi-script)

- **Esquema** (`normalize.kaikki_entry`): acepta el Kaikki compacto (ipa/ety/ety_t/gloss) **y** el crudo de
  wiktextract (sounds/etymology_text/etymology_templates/senses). Los dumps eslavos/indo-iranios/celtas son crudos.
- **Script** (`normalize.detect_script`/`romanize`): el esqueleto sale del **IPA** → el alfabeto de la grafía es
  transparente (ruso мать, urdu مستقل, hindi तरण → esqueleto por IPA). La romanización char-por-char (cirílico/
  griego/devanagari) es solo para el **fallback ortográfico de protos** romanizables; script sin mapa → declara ''.
- **Arquitectura (Alejandro):** palabra → IPA (elaborar si falta) → esqueleto → OAS. El OAS es la ÚLTIMA capa.

## 3. Reglas de trabajo (de Alejandro)

- **Genealogía precisa:** Védico/Sánscrito = indoario ATESTIGUADO (no proto); Proto-Indo-Iranio (iir-pro) ≈
  "proto-ario" reconstruido; Avéstico = iranio, hermana del indoario. Los ancestros de cada familia son los
  protos reconstruidos; los antiguos atestiguados entran como miembros.
- **Diseño planeado, no parcheo reactivo.** Pre-flight (`ingest/preflight.py`) mide huecos ANTES de cargar.
- **Medir, no asumir** (biclase, campo semántico): la genealogía/el uso arbitran, no la superficie.
- **Marcar, no filtrar.** El corpus crece; nada se tira, se anota (`is_proper`, `core_valid`…).

## 3b. Capa G2P — elaboración de IPA (`ingest/elaborate_ipa.py`)

Capa 2 de la arquitectura: para formas SIN IPA de fuente, se ELABORA vía epitran (grafema→fonema) y se guarda
en `form.ipa_elab` (precedencia: `ipa_raw` de fuente > `ipa_elab`; `segment_kaikki` usa coalesce). Modelos
fiables: hi mr bn or pa si tg lv lt (+ ur parcial). **Validación anti-basura:** si la salida conserva
caracteres del script fuente (epitran no transliteró, típico en abjad urdu ی ہ ک), se DESCARTA — no se inventa.
Ganancia medida: **Letón 23%→96%, Panyabí 53%→94%, Hindi/Bengalí/Lituano/Tayiko→100%** (11.550 formas elaboradas).
Lenguas sin modelo epitran (Sánscrito/Osetio/Nepalí…) se cubren por el esqueleto ORTOGRÁFICO (romanize).

## 4. Huecos declarados (honestidad del corpus)

- **Cobertura de esqueleto (auditoría `tests/audit.py`), por familia:** báltico 98%, eslavo 98%, indo-iranio 90%,
  romance 63%, itálico 58%, céltico 49%, **germánico 34%** (el mayor hueco: English 450k con poco IPA y sin G2P —
  epitran-inglés requiere flite y su ortografía es profunda). El G2P NO cubre: abjad sin vocales (perso-árabe salvo
  IPA de fuente), ortografía profunda (inglés/francés), lenguas sin modelo epitran.
- Antiguos futuros (Védico/Avéstico) dependerán de esta capa + esqueleto ortográfico IAST.
- **Róticas retroflejas ɭ ɽ:** el documento las declara hueco abierto (biclase no decidida) — hoy caen en Λ.
- **Biclase:** apagada; pendiente la versión condicionada a genealogía.
- **Colexificación:** solo donde hay `concept_id` (Lexibank) — escasa fuera de romance.
- **2-ciclos de etimología** a nivel lengua (préstamos bidireccionales legítimos) → refinar a nivel palabra.

## 4b. Fuentes múltiples (PLAN §4 — no depender de una sola)

El corpus dejó de ser solo-Kaikki. Cada fuente entra tagueada (`form.source_id`, `cognate_set.source`,
`protoform_hypothesis.source_id`) y **coexiste** sin fusión frágil; el cruce entre fuentes queda como paso
analítico honesto (por glottocode/concepto), no como adivinanza.

- **IE-CoR** (`ingest/ingest_iecor.py`, Heggarty et al. 2023, *Science*): cognación EXPERTA/ORO independiente de
  Wiktionary. 152 doculectos IE, 170 conceptos básicos ligados a Concepticon, `justification` + `doubt` por miembro.
  Namespaced (`iec_<glottocode>` lects, `source_id='iecor'`). → 25.731 formas, **2.640 cognate_sets oro**, 23.400
  miembros. Concepto: 0 nuevos (todos ya en Concepticon).
- **LIV²** (`ingest/ingest_liv.py`, Rix et al. 2001, vía LiLa/LLOD CC-BY-SA-4.0): raíces verbales PIE con FUENTE
  académica — la capa que a Wiktionary le falta. 385 pares verbo-latino→raíz-PIE; **356 casados (92%)** con formas
  latinas de la BD (match por norma sin macrones + variante u/v clásica). Entra en `form_etymology` (414 aristas de
  linaje la→*PIE, `kind='herencia'`, `source_id='liv'`) y en `protoform_hypothesis` (1.165 hipótesis
  `model='LIV²'`, prob 0.9, `status='reconstruido'`) → materializa la **"múltiples PIE con fuente" del §3c**: p.ej.
  `bʰreg` tiene Kaikki `bʰreg` (0.5) Y LIV² `*bʰreg/ǵ-` (0.9) sobre el mismo cognate_set.
- **Red `cog` de Wiktionary** (`ingest/ingest_cog.py`): reescrita a **estrella POR ENTRADA** (no union-find). El
  union-find fusionaba transitivamente (cog A→B, B→C) creando un blob basura de 50.373 formas no relacionadas
  (üf, whisk, sausage…). Ahora cada entrada afirma SUS cognados, topado a ≤40; 75.794 sets, máx 40, media 3.8.
- **Anomalía corregida:** `la` (Latín) y `la·angustus·A·001` estaban mal etiquetados `source_id='iecor'` de un
  experimento previo → devueltos a `kaikki`.
- **Registro `source`:** wiktionary, iecor, liv, devaan, kroonen, lexibank, kaikki (con cita/licencia). Pendientes de
  ingesta: Lexibank/IDS/NorthEuraLex (densidad+conceptos), de Vaan/Kroonen (reconstrucción, no redistribuibles).

## 4c. El código va sobre la RAÍZ, no sobre la forma superficial (error de fondo corregido)

**Síntoma (Alejandro, en el visor):** `aleshores` (ca) daba código `Λ·Σ·Λ·Σ` sobre `l·z·r·s` = la palabra ENTERA,
cuando `aleshores < ad illās hōrās` es univerbación de tres morfemas y lo que importa es la RAÍZ `hōrās`. Ocurría
en TODAS las palabras.

**Diagnóstico (dos bugs):** (A) `recompute_skeleton.compute()` deriva `code` de `cons_skeleton` = la forma
superficial completa, SIEMPRE — ignoraba `core_skeleton` aun cuando existía (Erfinderin: core `f·n·d`, code salía
`Λ·Φ·Ξ·Θ·Λ·Ξ` = r·f·n·d·r·n). (B) solo 11% de las formas tenían raíz (`core_skeleton`): la morfología venía solo
de afijos Kaikki transparentes; heredadas/fusionadas básicas tenían 0. `morph.span_start` 100% NULL; `is_compound`
0,3%.

**Arreglo (método elegido por Alejandro: ETIMOLOGÍA con fuente, no reglas de flexión que inventan raíces):**
`ingest/decompose_morphemes.py` decompone usando SOLO lo que la etimología documenta —
· CASO A: `etymology_text` con cadena explícita `"From X + Y"` (Wiktionary ya segmenta) → afijo = con guion,
  RAÍZ = componente sin guion.
· CASO B: `form_etymology.parent_form` multipalabra (`ad illās hōrās`) → RAÍZ = cabeza de contenido (último token);
  determinantes/preposiciones = función.
Cada morfema recibe su esqueleto y su código; la raíz alimenta `core_skeleton` + marca `is_compound`. **497.477
formas decompuestas (40%), 1,02M morfemas → cobertura de raíz 11%→46%.** `aleshores` → `ad`(Θ)·`illās`(Λ·Λ·Σ)·
**`hōrās`(Λ·Σ, raíz)**. Nota honesta: el token es el acusativo plural del etymon (por eso queda la -s); la
lematización raíz→hōra queda pendiente. Columnas nuevas: `morph.code/cons_skeleton/surface/morph_ord/source_id`.

**Visor:** el análisis endolingüístico ahora LIDERA con el código de la RAÍZ y desglosa por morfema (raíz marcada);
donde no hay segmentación etimológica, dice honestamente "código (forma superficial) — raíz sin segmentar aún".
Además: nombre de lengua junto al ISO (cognados/etimología) y fuentes agregadas por forma (corroboración visible:
`fingo < *dʰeyǵʰ- · kaikki, liv`).

## 4d. Densidad + concepto + linaje + contacto (los tres "Ahora")

- **IDS + NorthEuraLex → capa de CONCEPTO (3.2%→30.2%).** El mayor hueco estructural era el concepto (sin él, no
  hay comparación translingüe ni colexificación). Se ingirieron dos wordlists CLDF basadas en conceptos: IDS
  (`cldf_ingest.py`, 437.902 formas / 320 lenguas / 1.310 conceptos) y NorthEuraLex (`ingest_csv_wordlist.py` —
  loader CSV directo, porque NEL no trae metadata json; 121.611 formas / 107 lenguas / 956 conceptos). Ambas
  reconcilian lengua por glottocode y concepto por concepticon_id, con `is_loan` desde la columna `Loan`. Total de
  formas 1,42M→1,98M. Nota honesta: el 30% de concepto viene de ESAS fuentes; las formas Kaikki siguen sin concepto
  (mapear sentidos Kaikki→Concepticon es tarea aparte).
- **Parser de PROSA etimológica → linaje estructurado** (`parse_etymology_prose.py`). 96% tiene etimología en prosa
  pero solo 30% tenía aristas. El parser lee la CLÁUSULA PRINCIPAL ("Inherited/Borrowed/From <Lengua> <forma>"),
  gazetteer de 737 nombres (lect.name ≥4 + alias de ancestros; crea ancestros faltantes: enm, cu, got, gmw-pro…),
  alta precisión. **+41.529 aristas** (`source_id='kaikki-prose'`), linaje 30%→34%. **Hallazgo:** el 66% "sin
  linaje" NO es herencia faltante — es *word-formation* misma-lengua ("From minimal + -ité", "coat + hook", los
  árboles "Etymology tree" derivacionales), que ya vive en la capa de MORFOLOGÍA. El grafo genealógico está más
  completo de lo que el % sugiere.
- **Contacto: préstamos marcados.** Había 197.983 aristas `prestamo` pero `form.is_loan=0`. Propagado →
  **186.657 formas** marcadas como préstamo (+ `Loan` de IDS/NEL).
- **Integridad:** QA 27 OK / 0 fallos (4 ⚠️ = duplicados cross-fuente esperados). Cero huérfanos, cero violación de
  licencia, toda forma con lect+fuente.

## 4e. Ramas IE faltantes: Helénico, Albanés, Armenio, Tocario (Anatolio no disponible)

Descargadas de kaikki.org (no estaban en disco) y cargadas por `add_family.sh`:
- **Helénico**: Ancient Greek (grc, 20.861), Greek (el, 18.264), Mycenaean (gmy, 495). Alfabeto griego → romanize.
- **Albanés**: Albanian (sq, 11.327). Gheg/Tosk/Arbëresh no tienen dump propio en Kaikki.
- **Armenio**: Armenian (hy, 19.398 vía IPA 90%), Old Armenian (xcl, 6.189), Middle Armenian (axm, 419).
- **Tocario**: Tocharian B (txb, 3.368), Tocharian A (xto, 1.107). Corpus pequeño, ya romanizado (Latin).

**Anatolio — recuperado del DUMP CRUDO.** kaikki.org no lo sirve como extracto propio (índice de 463 lenguas), pero
sí está en `raw-wiktextract-data.jsonl.gz` (**2.84GB comprimido** = todo Wiktionary-EN). Se transmitió con
`curl | gzip -dc | grep` filtrando `lang_code` al vuelo (sin guardar los ~30GB descomprimidos) y luego se ruteó por
`lang_code` de NIVEL SUPERIOR en Python (el grep es colador grueso: captura líneas que MENCIONAN el código en
descendientes/cognados; el idioma real es el top-level). Resultado: Hittite 378, Luwian 85, Carian 57, Lydian 51,
Lycian 47, +Palaic/Milyan/Sidetic. **Bonus:** protos que faltaban — Proto-Helénico (236), Proto-Albanés (214),
Proto-Anatolio (30) → cargados a sus familias. Esqueleto anatolio BAJO por diseño: buena parte de Hittite está en
**cuneiforme** (𒀸 𒂍…) sin romanización; los transliterados a latín (ūk, ḫalukaš) sí. Lydian/Carian usan alfabetos
propios (sin mapa). DATA (formas/sentidos/etimología) presente; el esqueleto/OAS es capa aplazada. Proto-Armenio/
Proto-Tocario no aparecen como entrada propia en el dump (solo mencionados).

Correcciones que estas ramas destaparon:
- **Clasificador OAS**: guturales epiglotales/faríngeas caucásicas **ʜ ʡ ʢ** (Chechen, vía NorthEuraLex) → hub Χ;
  clic **ʘ** → IGNORE; separador de frase **`#`** de iecor → BOUNDARY. (No eran de las ramas IE, sino fallout de NEL.)
- **Mapa de romanización ARMENIO** (`_ARM` en `normalize.py`) — no existía. Desbloquea Old/Middle Armenian (sin IPA)
  de 0%→100% esqueleto vía ortográfico. APROX declarada: africados ts/dz/č/ǰ → Σ (release sibilante), refinable.
- **Nombres de lect** corregidos (el load creaba name=código): grc/el/gmy/sq/hy/xcl/axm/xto/txb con nombre real y
  family='Indo-European'. `xcl` estaba mal nombrado "Classical Arabic" (las FORMAS sí eran armenias) → "Old Armenian".
- **1 forma corrupta** borrada (el `μα την Παναγία` con IPA malformada mezclando texto inglés + griego crudo).

## 4f. Red de significado: COLEXIFICACIÓN global (PLAN §3, red #3)

Estaba en 0 (el builder `build_colex.py` era por-familia y solo veía Lexibank; concepto al 3%). Tras IDS/NEL/iecor
(597k formas con concepto) se escribió `build_colex_global.py` (estilo CLICS, cross-lingüístico): en UNA lengua,
misma forma (clave NFC) → ≥2 conceptos Concepticon = colexificación (a,b,lect). Tope MAXC=15 conceptos/forma
(anti-ruido). → **63.323 colexificaciones · 19.830 pares de concepto · cientos de lenguas.** Validación: los pares
más frecuentes son los UNIVERSALES conocidos (moon/MONTH 192, foot/leg 177, tree/WOOD 146, skin/LEATHER, tongue/
LANGUAGE, hand/ARM, earth/LAND…) → el cómputo es correcto. El peso cross-lingüístico de un par = nº de lenguas que
lo colexifican (query sobre `colex`).

**Extensión a Concepticon a nivel SENTIDO** (`map_concepticon.py`): mapear un solo `concept_id` por FORMA daba error
en polisémicas (foot→PAY por el sentido "foot the bill"; se elegía la variante más corta). Corregido: se mapea cada
SENTIDO a su concepto (normalización de palabra: quita artículos/"to"/paréntesis, parte por ;,/, gloss_en+
concepticon_gloss, solo variantes NO ambiguas). `form.concept_id` solo si la forma es inequívoca (1 concepto);
polisémica → NULL (el significado vive en los sentidos). → 292k sentidos mapeados. La colexificación ahora toma
conceptos de FORMA (wordlists + inequívocas) Y SENTIDO (polisemia Kaikki): **138.064 colexificaciones, 62.454 pares**.
Concepto en formas 3%→**38.8%**. Nota Kaikki: muchas glosas de sustantivos básicos son DEFINICIONES largas (no el
lema), así que no auto-matchean — honesto: mejor sin concepto que uno errado.

**Visor:** sección "Red de significado (colexificación · todas las fuentes)" — muestra los conceptos de la palabra
(sus sentidos) y con qué conceptos se colexifica cross-lingüísticamente, con nº de lenguas y de FAMILIAS (señal de
universalidad cross-fuente): p.ej. `sol→sun` colexifica `day` (63 lenguas, 22 familias). Además el bloque de
COGNADOS se unificó a una sola lista deduplicada (clave NFC) con insignia de fuente — se acabaron las tarjetas
repetidas y los duplicados Unicode (`fr mère ×3`).

## 4g. Linaje hasta PIE (§3/§3f — "toda la historia de la palabra")

Problema (Alejandro): muchas palabras llegaban a su proto de rama pero no a PIE. Diagnóstico y arreglos:
- **gem-pro/itc-pro tenían 0 etimología** (cargados antes del fix de esquema raw, como el bug del eslavo) → recargados
  → 0→3.833 aristas a PIE.
- **Protos intermedios sin entradas** (destino de miles de aristas, 0 filas): gmw-pro (17.972 aristas), cel-pro,
  iir-pro, ine-bsl-pro, cel-bry-pro → descargados de Kaikki y cargados con su etimología→PIE.
- **Formato "Etymology tree"** (101k formas, sobre todo inglés): la etimología estaba como árbol multilínea +
  cadena en prosa "from…from…from PIE", SIN templates → el loader no creaba aristas. `parse_etymology_chain.py`
  extrae toda la cadena → +347k aristas (father: `ang→enm→gmw-pro→gem-pro→ine-pro *ph₂tḗr`).
- **iecor root_forms** (`ingest_iecor_lineage.py`): raíz PIE experta por cognate set (no-Kaikki) → +20.744 aristas.
- **Encadenado** (`resolve_lineage.py`): `parent_form` (texto) → `parent_form_id` (entrada real) con normalización de
  diacríticos + alias de variantes (la-vul→la) → 48% resueltas; permite el walk recursivo hijo→…→PIE.
- **Vista en el visor**: sección "Etimología · toda la historia" con la cadena completa sangrada e insignia
  "llega a PIE ✓" (walk recursivo cycle-safe).

- **Pokorny IEW (StarLing/Starostin)** (`scrape_pokorny.py` + `ingest_pokorny.py`): raspado de las 2.222 raíces PIE
  del CGI de starlingdb.org (2.140 obtenidas; ~82 se resisten a 502 intermitentes). Cada raíz = forma PIE + glosa +
  reflejos por rama. Ingiere **2.140 raíces PIE expertas** como protoform_hypothesis (model='Pokorny') + **3.895
  aristas reflejo→PIE** casadas (sobre todo Latín 2.375 y sla-pro 973 — la transcripción erudita solo casa bien en
  mismo alfabeto). **FUENTE EN CUARENTENA**: adiciones de Starostin CC-BY-NC-ND → source.redistributable=FALSE (PLAN
  §5). Primer diccionario etimológico PIE no-Wiktionary en el corpus.

**Resultado: formas que alcanzan PIE 41k → 158.299 (3.9×)** esta sesión. Cobertura honesta por antigüedad: Sánscrito
78%, Lituano 50%, Celta(cy) 42%, Latín 43%; modernas ~18-24% (techo real: mucho léxico no tiene étimo PIE
documentado, o su proto no lo tiene). Subir más requiere Pokorny (CLDF público, descargable) o de Vaan/Kroonen
(copyright). Columnas: `form_etymology.parent_form_id`.

## 4h. Densidad Lexibank + limpieza de genealogía

- **Lexibank completo** (`ingest_csv_wordlist.py`, COPY): **1.740.092 formas · 5.501 lenguas · 3.205 conceptos**
  (con segmentos, cognacy, CV). Total del corpus 2,06M→**3,78M formas**, lenguas 556→**3.404**, concepto 39%→**66.6%**,
  colexificación 138k→**223.428** (escala CLICS real, cientos de familias). Costo en disco REAL: solo **+0,33 GB**
  (base = forma+concepto+is_loan+segmentos-array vía COPY; sin segment/skeleton/crypto rows) — mucho menor que el
  estimado conservador de 1,5 GB. El pipeline completo (esqueleto/crypto sobre Lexibank) añadiría ~4,8 GB si se corre.
- **Esqueleto sobre Lexibank** (corrido): **1.739.994 esqueletos** (99,99%) → corpus con 3,08M esqueletos (82%).
  Costo real solo **+0,44 GB** (el esqueleto es barato; las caras son segment/crypto/morph, no corridas). Sin
  clasificar 0,44%→**0** tras mapear extensiones sinológicas/SE-asiáticas (ɿ ʅ vocales apicales; ȵ ȴ ȶ ȡ
  alveolopalatales; ∼ ~ ⁿ nasalización); los modificadores IPA (ejectivo ˀ, faringalizado ˠ, labializado ʷ) se
  despojan y la consonante base clasifica.
- **Limpieza de genealogía** (Latín/Romance parecía "desactualizada"): eran **duplicados** (misma arista de varias
  fuentes/pasadas: kaikki+kaikki-tree+kaikki-prose+pokorny) y **malformadas** (parent_form vacío). Borradas 22.284
  vacías + 311.785 duplicadas → 1,26M→**923k aristas** limpias. Ejemplo: `padre → osp padre → la pater/patrem →
  itc-pro *patēr → ine-pro *ph₂tḗr` sin ruido. PIE-reach 151.353.

## 5. Familias cargadas

Registro en `ingest/families.py`. Estado: **12 familias, ~2.05M formas, 551 lenguas, QA 27 OK/0.**
romance · italic · germanic · slavic · indo-iranian · celtic · baltic · hellenic · albanian · armenian · tocharian · **anatolian**.
Todas las ramas IE presentes. Fuentes coexistiendo: kaikki · ids · nel · iecor · lexibank (+ liv, kaikki-prose en linaje).
