# Estrategia de escalado — más lenguas y sistemas lingüísticos (familias)

## 1. Dónde estamos (2026-08-05)
- **Familias ingeridas: 1** (Indo‑Europeo). **Lenguas con datos reales: 9** (Latín + Español, Italiano, Francés,
  Portugués, Catalán, Rumano, Napolitano; + protos/estadios como nodos‑ancestro sin formas).
- 388 lects totales (355 lengua, 31 proto‑rama, 2 PIE), pero solo 9 con formas. `macrosystem` coarse
  (indo‑europeo/semítico) — **sin árbol de sub‑ramas** todavía.
- Todo el pipeline (ingesta CLDF, Kaikki, segmentación IPA, esqueleto+vocales+acento, afijos, core_skeleton,
  reconciliación por glottocode, QA) **ya generaliza** — escalar = re‑correrlo por lengua/familia.

## 2. Qué hay disponible para crecer
- **Kaikki (48 lenguas, ya descargadas):** IE denso — Germánico (English, German, Dutch, Gothic, Old English/High
  German/Norse, Icelandic, Swedish, Danish, Faroese, Frisian, Yiddish, Scots, Low German, Luxembourgish), Eslavo
  (Russian, Polish, Czech, Slovak, Slovene, Bulgarian, Ukrainian, **Proto‑Slavic**), Romance (Italian, French,
  Portuguese, Catalan, Romanian, Occitan, Sardinian, Sicilian, Neapolitan, Galician, Aromanian, Friulian, Ladin,
  Walloon, Old French/Spanish), **protos** (Proto‑IE, Proto‑Germanic, Proto‑Italic, Proto‑Slavic) — **+ Swahili
  (Bantu, primer NO‑IE)**. Traen etimología+morfología+sentidos+IPA (con acento).
- **Lexibank / CLDF (5.500 lenguas, ya descargado):** breadth mundial — TODAS las familias (Austronesio, Sino‑Tibetano,
  Afroasiático, Níger‑Congo, Australiano, Amazónico…). Vía **pycldf** (loader único). Da wordlists (segmentos+cognación),
  no la riqueza etimológica de Kaikki.
- **Glottolog:** el ÁRBOL genealógico (familias/sub‑ramas) — lo que falta para clasificar bien.
- **ASJP (~7.000 lenguas):** listas cortas → esqueleto de cobertura casi total.

## 3. Plan por fases
**Fase 1 — profundizar IE con Kaikki (fácil, alto valor):**
1a. **Cargar el resto de Kaikki IE** (Germánico + Eslavo + resto Romance + protos) con el pipeline actual. Desbloquea:
   resonancia de esqueleto **cross‑rama REAL** (Angst↔angostura de datos, no seed), cognación IE amplia, y estadios
   atestiguados (Old English/High German/Norse, Gothic) para el trabajo dirigido/linaje.
1b. **Ingerir Glottolog** → asignar cada lect a su **familia/sub‑rama** real (arregla el macrosystem coarse; da el
   árbol). Vía pycldf (glottolog‑cldf, CC BY 4.0).
1c. **Primer no‑IE con Kaikki: Swahili** (Bantu) → probar el pipeline fuera de IE (esqueleto, tono, morfología).

**Fase 2 — breadth por familia (Lexibank/CLDF, pycldf):** ingerir familias enteras (Austronesio vía ABVD,
Sino‑Tibetano vía STEDT, etc.) como wordlists. Cobertura mundial de forma+cognación; sin etimología profunda.

**Fase 3 — hacia todas las lenguas:** ASJP para el esqueleto de cobertura; profundizar por familia según interés
(el corpus no se termina — se crece por prioridad).

## 4. Qué revisar al salir de IE (para no romper el pipeline)
- **Esqueleto/OAS:** el mapeo IPA→clase está afinado para consonantes IE. Revisar para **clicks** (khoisan),
  **implosivas/eyectivas**, **tonos** (ya capturamos tono en la vocal; validar), **retroflejas** (indoario, dravídico).
- **Morfología no‑concatenativa:** Semítico (raíz‑y‑patrón) ya en el diseño; activar al ingerir árabe/hebreo con formas.
- **Acento/prosodia:** Kaikki trae acento para muchas; tonales necesitarán fuente de tono (PHOIBLE).
- **Reconciliación:** por glottocode siempre; Kaikki ISO ↔ glottocode necesita el mapa (ampliar ISO→glottocode).
- **Licencias:** cada dataset Lexibank con su licencia (algunos NC → cuarentena).

## 5. Recomendación inmediata
**Fase 1a (resto de Kaikki IE) + 1b (Glottolog).** Es el mayor salto de valor con lo que YA tenemos descargado, sin
salir de IE (donde el pipeline está probado), y **da por fin el árbol de familias/sub‑ramas real**. La resonancia
cross‑rama (itálico↔germánico↔eslavo) se vuelve consultable sobre datos, no sobre el seed.
