# Carga de la familia Germánica — reporte

*Multi-familia funcionando: Romance + Itálico + Germánico coexisten. QA 26 OK / 0 fallos.*

## Censo

| | |
|---|---|
| **Familias (cognados)** | romance **19.882** · italic **603** · germanic **27.068** |
| **Formas totales** | **1.165.994** en 39 lenguas |
| **Capas germánicas** | 88.843 miembros cognados · 31.666 correspondencias · 451.839 enlaces de polisemia · 27.068 proto-formas · 54.334 préstamos / 559 cohortes · 694 fonemas con rasgos |
| **Esqueletos** | 517.352 · 86.754 códigos-linaje únicos · **0 residuales `?`** |

Lenguas germánicas cargadas (19): en, de, nl, sv, da, nn, is, af, fy, lb, yi, got (gótico), ang (inglés
antiguo), goh (alto alemán antiguo), non (nórdico antiguo), nds (bajo alemán), fo (feroés), sco (escocés),
gem-pro (proto-germánico). Osco/Falisco/Middle-* sin dump → quedan como ancestros etimológicos.

## Resonancia cross-familia — raíz PIE \*pₐtḗr 'padre'

Mismo código **Φ·Θ·Λ** en Romance *y* Germánico; la **Ley de Grimm** aparece como *mutación dentro de la
clase* (no cruza de clase, por eso el código se conserva):

| Lengua | Forma | Esqueleto | Código |
|---|---|---|---|
| Latín | pater | p·t·r | **Φ·Θ·Λ** |
| Español / Italiano | padre | p·d·r | **Φ·Θ·Λ** |
| Alemán | Vater | f·t·r | **Φ·Θ·Λ** |
| Inglés | father | f·ð·r | **Φ·Θ·Λ** |
| Islandés | faðir | f·ð·r | **Φ·Θ·Λ** |

p→f (ambas **Φ** labial) · t→θ/ð (ambas **Θ** dental) · r→r (**Λ** líquida).

## Bugs corregidos durante la carga (todos de escalabilidad, en GitHub)

1. **Perf CRÍTICO** — borrado O(n·m) por 15 columnas-FK sin índice (colgaba 90 min en `crypto.skeleton_id`
   y `polyseme_link.sense_a/b`) → indexadas todas; reload de English **90 min → ~30 s**. Borrado incremental
   set-based en `kaikki_ingest` en vez de cascade por-fila.
2. **Multi-familia** — temp table `ON COMMIT DROP` (borraba la tabla tras el 1er archivo), patrón `&&…||`
   que enmascaraba fallos, FK de afijos sin garantía de lect.
3. **OAS (inventario germánico)** — 12.087 esqueletos con `?` → **0**: vocales ʏ ɶ ɞ ᵻ ᵿ, consonantes
   ʍ→Φ / ɧ→Χ / ɬ ɮ ǁ ɺ→Λ, y marcas de tono/entonación (superíndices, flechas) → `IGNORE`.

## Redes semánticas de coderivados → `coderiv-networks.md`

Ver el archivo hermano: **910 redes** de coderivados que conservan **etymon + código OAS + campo semántico**
cruzando Germánico↔Itálico/Romance.
