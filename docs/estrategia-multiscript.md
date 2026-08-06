# Estrategia multi-script y multi-esquema (para escalar a miles de lenguas)

Al crecer más allá del núcleo indoeuropeo latino aparecen dos heterogeneidades. La capa
`ingest/normalize.py` las absorbe.

## 1. Esquema de la fuente

Kaikki viene en dos formatos y hay que aceptar ambos:

| | compacto | crudo (wiktextract) |
|---|---|---|
| forma | `word` | `word` |
| pronunciación | `ipa:[…]` | `sounds:[{ipa}]` |
| etimología | `ety`, `ety_t:[{n,a}]` | `etymology_text`, `etymology_templates:[{name,args}]` |
| sentidos | `gloss:[…]` | `senses:[{glosses}]` |

`normalize.kaikki_entry(d)` devuelve **siempre** la forma compacta. Los dumps eslavos (y muchos otros)
son crudos; los romances/germánicos que teníamos eran compactos.

## 2. Sistema de escritura (script)

**Principio rector: el esqueleto OAS sale del IPA, que es INDEPENDIENTE del script.** Ruso en cirílico,
Hindi en devanagari o alemán en latín dan el mismo objeto endolingüístico *mientras Kaikki traiga IPA* —
y casi siempre lo trae (en `sounds`). Prueba: el ruso **мать** (cirílico) produce el esqueleto **Ϻ·Θ**
desde su IPA, idéntico a lat. *mater*, al. *Mutter*, esp. *madre* (**Ϻ·Θ·Λ**) — la raíz PIE de 'madre'
a través de cuatro ramas y tres alfabetos.

El script **solo** importa en el *fallback ortográfico* — lenguas antiguas/proto SIN IPA (Proto-Eslavo,
Proto-Germánico…). Ahí:

- `normalize.detect_script(text)` identifica el script por rangos Unicode.
- `normalize.romanize(text)` translitera **char por char** (mapa combinado) las consonantes a latín —
  basta para la clase OAS, que es gruesa (labial/dental/velar/sibilante/líquida/nasal). Maneja formas de
  **script mezclado** (latín + cirílico embebido, típico en reconstrucciones).
- Scripts sin mapa aún (árabe, han, hangul) → devuelve `''`: **declara el hueco, no inventa**.

Alcance actual del fallback: **latín, cirílico, griego, devanagari** (consonantes). El esqueleto
ortográfico se aplica SOLO a protos/antiguas romanizables (`skeleton_from_ortho.py <lect-proto>`), NUNCA a
lenguas de ortografía profunda (inglés), donde la grafía no es proxy fonémico y el IPA manda.

## Reglas de oro al añadir una familia de otro script

1. **Confía en el IPA.** Si la fuente trae IPA, el script de la grafía es irrelevante para el esqueleto.
2. **Ortografía solo como último recurso**, y solo para protos/antiguas romanizables; declara el hueco si no.
3. **Amplía `normalize._MAPS`** con el script nuevo (consonantes) cuando aparezca un proto sin IPA en él.
4. **Amplía el inventario OAS** (`recompute_skeleton.py`: IPA/VOW/IGNORE) para los símbolos IPA nuevos del
   inventario fonético de la familia — cada rama trae algunos (germánico: ʏ ʍ ɧ tono; eslavo: yers ъ ь,
   palatalización opcional ⁽ʲ⁾). El QA (`SKEL · residual '?'`) los caza.
