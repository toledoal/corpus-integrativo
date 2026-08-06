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

## 4. Huecos declarados (honestidad del corpus)

- **Cobertura de esqueleto por IPA** parcial en lenguas con poco IPA en Wiktionary (célticas menores 24–58%,
  urdu 69%, iranias menores por ver) → **pendiente la capa G2P** (elaboración de IPA) que recupera el residuo y
  será imprescindible para los antiguos (Védico/Avéstico).
- **Róticas retroflejas ɭ ɽ:** el documento las declara hueco abierto (biclase no decidida) — hoy caen en Λ.
- **Biclase:** apagada; pendiente la versión condicionada a genealogía.
- **Colexificación:** solo donde hay `concept_id` (Lexibank) — escasa fuera de romance.
- **2-ciclos de etimología** a nivel lengua (préstamos bidireccionales legítimos) → refinar a nivel palabra.

## 5. Familias cargadas

Registro en `ingest/families.py`. Estado: **6 familias, ~1.31M formas, 54 lenguas, QA 26 OK/0.**
germanic · romance · slavic · indo-iranian · celtic · italic. (Indo-iranio en expansión: iranias modernas.)
