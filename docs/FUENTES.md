# Fuentes, atribución y licencias — Corpus Integrativo

**Qué es este proyecto y qué NO es.** El Corpus Integrativo **no genera datos lingüísticos primarios**: **integra**
fuentes existentes —cada una con su propia autoría y licencia— en una sola base consultable para **correr
experimentos** de lingüística histórica/comparada. Toda forma, sentido y arista de linaje lleva su `source_id`
(procedencia obligatoria; 0 datos sin fuente). No redistribuimos las fuentes: las citamos y respetamos su licencia.

Este documento es la declaración de atribución y cumplimiento. La tabla `source` de la BD es la fuente de verdad
(cita, url, licencia, `redistributable`).

## Postura de licencias

- **CC-BY / CC-BY-SA / CC-BY-4.0** (redistributable=TRUE): se usan con **atribución**; para **ShareAlike (CC-BY-SA)**,
  cualquier redistribución de derivados hereda la misma licencia. Son la mayoría de nuestras fuentes.
- **Copyright / CC-BY-NC-ND** (redistributable=FALSE): **EN CUARENTENA.** Se ingieren solo para uso interno de
  investigación (fair use / cita académica); **nunca se exportan, publican ni redistribuyen** como datos. Cualquier
  volcado público del corpus debe **excluir** las filas con `source_id` de estas fuentes (filtro
  `WHERE redistributable`). Aplica a: **Pokorny (CC-BY-NC-ND)**, **de Vaan (copyright)**, **Kroonen (copyright)**.

## Fuentes de DATOS

| source_id | Fuente / cita | Aporta | Licencia | Redistrib. |
|---|---|---|---|---|
| `kaikki` / `wiktionary` | Wiktionary (inglés) vía **Kaikki.org / wiktextract** (Ylönen) | formas, IPA, sentidos, etimología, morfología | CC-BY-SA-3.0 | ✅ (SA) |
| `kaikki-prose` / `kaikki-tree` | Derivado nuestro: parseo de la etimología en prosa/árbol de Wiktionary | aristas de linaje estructuradas | CC-BY-SA-3.0 | ✅ (SA) |
| `lexibank` | **Lexibank** (List, Forkel, Greenhill et al. 2022; CLDF/CLTS) | densidad (1.74M formas, 5.5k lenguas), segmentos, cognacy | CC-BY-4.0 | ✅ |
| `ids` | **IDS** — Intercontinental Dictionary Series (Key & Comrie eds.) | amplitud semántica por concepto | CC-BY-4.0 | ✅ |
| `nel` | **NorthEuraLex** (Dellert et al. 2020) | wordlist Norte de Eurasia por concepto | CC-BY-4.0 | ✅ |
| `iecor` | **IE-CoR** (Heggarty et al. 2023, *Science*) | cognación EXPERTA/oro IE, root-forms PIE | CC-BY-4.0 | ✅ |
| `liv` | **LIV²** (Rix et al. 2001), LLOD vía LiLa/CIRCSE | raíces verbales PIE con fuente | CC-BY-SA-4.0 | ✅ (SA) |
| `pokorny` | **Pokorny 1959, IEW**; digitización Starostin/StarLing | 2.140 raíces PIE + reflejos | **CC-BY-NC-ND-3.0** | ❌ cuarentena |
| `devaan` | de Vaan 2008, *EDL* (Brill) | reconstrucción latín→PIE | **copyright** | ❌ (no cargado) |
| `kroonen` | Kroonen 2013, *EDPG* (Brill) | reconstrucción germánico→PIE | **copyright** | ❌ (no cargado) |

## ESTÁNDARES usados (no son fuentes de forma, sino de identificadores/clasificación)

| source_id | Estándar | Uso | Licencia |
|---|---|---|---|
| `concepticon` | **Concepticon** (List et al.) | `concept.concepticon_id` — nodo de concepto | CC-BY-4.0 |
| `glottolog` | **Glottolog** (Hammarström et al.) | `lect.glottocode`, familia/rama | CC-BY-4.0 |
| `clts` | **CLTS/BIPA** (List et al.) | referencia de transcripción IPA | CC-BY-4.0 |

## Reglas operativas de cumplimiento

1. **Procedencia obligatoria:** toda fila con dato lleva `source_id`; QA verifica 0 huérfanos de fuente.
2. **Cuarentena NC/ND/copyright:** cualquier export/publicación filtra `redistributable=TRUE`. Pokorny/de Vaan/
   Kroonen se quedan dentro para experimentos, fuera de cualquier volcado.
3. **ShareAlike:** un derivado redistribuido que incluya datos CC-BY-SA se publica bajo CC-BY-SA.
4. **Atribución:** este documento + la tabla `source` acompañan cualquier resultado/publicación.
5. **Sin datos primarios inventados:** no se imputan formas/étimos "en silencio"; lo derivado (esqueleto, colex,
   linaje parseado) se marca con su `source_id` propio y se recomputa del núcleo.
