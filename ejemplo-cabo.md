# Entrada trabajada: **cabo** (español) — POLISEMIA rica (≥4 sentidos) de un solo étimo

Sexto ejemplo, elegido para estresar la **red polisémica** (≥4 sentidos radiando de *un* étimo, latín *caput*
'cabeza'). Bonus: muestra **lenición** (p→b) y un núcleo que **muta + trunca**, y el matiz **código‑de‑clase vs
segmento**.

---

## 0. Identidad
- **form_id:** es·cabo·N·001 · **lect:** Español → Ibero‑Romance → Romance/Itálico → Indo‑Europeo
- **concepto base (Concepticon):** END / TIP (radiando; ver §7) · **IPA:** [ˈka.βo] · acento: penúltima
- **fuente:** DLE; Corominas s.v. *cabo* (< lat. *caput* 'cabeza')

## 1–2. Forma y morfología
- segmentos: k·a·β·o → consonantes **k, b(β)** · morfología: raíz **cab‑** + **‑o** (desinencia masc.)

## 3. Esqueleto — **código en SÍMBOLOS, núcleo en LETRAS** (convención fijada)
- **código canónico de la PALABRA (símbolos de clase):** **Χ · Φ**  (k→Χ velar, b→Φ labial‑oclusiva)
- **núcleo/raíz (en LETRAS):** **k · b**  (raíz cab‑, sin la desinencia ‑o)
- **skeleton_id:** SK·es·cab·001

## 4. Correspondencia lat *caput* → esp *cabo* — lenición + truncamiento, y el matiz de NIVEL
| pieza | latín *caput* | esp *cabo* | tipo |
|---|---|---|---|
| C1 | k | k | **conservar** (Χ=Χ, segmento k=k) |
| C2 | p | b (β) | **mutar segmento** (lenición intervocálica p→b) — **pero CONSERVA la clase** (p y b ∈ Φ) |
| C3 | t | ∅ | **truncar** (pérdida de ‑t final) |
| V/desin. | ‑ut | ‑o | (vocálico/morfológico) |

**Matiz de diseño:** la lenición *p→b* es **mutación de SEGMENTO** pero **conservación de CÓDIGO‑de‑clase** (ambos
son Φ). ⇒ `corr_type` necesita un **nivel**: clase‑código (Χ·Φ conservado) vs segmento (p→b mutado). El truncamiento
del ‑t sí es pérdida a ambos niveles. *(refina §6g del PLAN)*

## 5. Genealogía (breve)
- cabo < lat. **caput** 'cabeza' < PIE **\*kaput‑ / \*kapōl‑** 'cabeza' *(reconstrucción con variantes → distribución;
  fuentes: de Vaan, LIV/NIL)*. Herencia recta, sin sustrato.

## 6. Cognados (red de la FORMA) — familia *caput*
- esp: **cabeza** (< *capitia*), **cabecera, cabecilla, caudillo** (< *capitellum*), **capital, capitán** (cultismos)
- otras lenguas: it. *capo*, fr. *chef* (!) / *cap*, ingl. **chief, chef, cape, captain, capital** (vía francés/latín),
  al. *Kaputt*? (no; *Haupt* 'cabeza' es el cognado germánico nativo por Grimm k→h)
- **nota cruzada:** ingl. *cape* (accidente geográfico) es **el mismo étimo** que la acepción 2 de *cabo* → cognado Y
  co‑sentido.

## 7. ⭐ Red POLISÉMICA — ≥4 sentidos radiando de 'cabeza→extremo'

| # | sentido | ejemplo | ruta desde *caput* 'cabeza' |
|---|---|---|---|
| 1 | **extremo, punta, final** | *al cabo de tres días*; *cabo de vela* | cabeza → extremo/punta |
| 2 | **accidente geográfico (cabo)** | *Cabo de Hornos* | "cabeza" de tierra que entra al mar |
| 3 | **grado militar (cabo)** | *el cabo primero* | "cabeza" de una escuadra (jefe de unidad pequeña) |
| 4 | **cuerda / cabo náutico** | *largar un cabo* | extremo → soga (metonimia náutica) |
| 5 | **locuciones** | *llevar a cabo, al fin y al cabo, atar cabos* | 'fin/extremo' lexicalizado |

- **estructura de la red:** es **polisemia radial** (todos de un solo étimo *caput*), NO homonimia. El corpus debe
  marcar `polysemy` (un étimo, varios sentidos) frente a `homonymy` (varios étimos, misma forma) — distinción que
  toca la capa genealógica.
- **sinónimos NO cognados** por sentido: (1) *extremo, punta, final*; (2) *promontorio, punta*; (3) *sargento*(≈);
  (4) *soga, cuerda, maroma*. Cada acepción tiene su propia vecindad de sinónimos.
- **colexificación:** *cabo* colexifica {extremo ↔ cabo‑geográfico ↔ jefe‑militar ↔ soga} — un abanico que el
  `polyseme_link` + `colex` deben registrar como **un nodo‑forma con múltiples `sense`**, cada sentido con su concepto.

## 8. Qué añade al DISEÑO
1. **Polisemia radial de ≥4 sentidos** = una `form` con **múltiples `sense`**, cada uno con su `concept`, unidos por
   `polyseme_link`; y cada sentido con su propia vecindad de sinónimos. La red polisémica no es un enlace, es un
   **abanico por entrada**.
2. **Polisemia ≠ homonimia** — el corpus debe distinguir "un étimo, varios sentidos" (cabo) de "varios étimos, misma
   forma" (p.ej. ingl. *bank* financiero vs *bank* de río). La diferencia vive en si los `sense` comparten
   `cognate_set`/étimo o no. ⟨nuevo campo/flag⟩
3. **`corr_type` tiene NIVEL:** clase‑código vs segmento (lenición p→b conserva clase, muta segmento). El esqueleto
   puede "conservarse" en símbolos y "mutar" en letras — ambos se guardan.
4. Reengancha con transformations: la lenición intervocálica p→b es otra ley recuperable (como k→θ de *lanza*).
