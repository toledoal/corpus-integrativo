# Entradas trabajadas: **sub‑** y **‑less** — los AFIJOS como entradas de primera clase

Séptimo ejemplo. Decidimos que el esqueleto del núcleo **excluye** afijos — pero los afijos **sí son entradas**, con
su propia historia, sentido y esqueleto. Aquí modelamos un prefijo (*sub‑*) y un sufijo (*‑less*), y cómo se enlazan
con las palabras que los usan.

---

## A. Prefijo **sub‑**

- **morph_id:** afx·sub·PREFIX·001 · **tipo:** prefijo · **categoría:** varía (no cambia clase por sí solo)
- **función/sentido:** 'debajo, bajo, subordinado, secundario, casi' (submarino, subsuelo, subconsciente)
- **esqueleto propio:** código **Σ · Φ** (s→Σ, b→Φ) · núcleo en letras **s · b**
- **genealogía:** lat. **sub** 'bajo' < PIE **\*(s)up‑ / \*upo** 'debajo, desde abajo' *(cognado de ingl. up, gr.
  hypo‑, scr. upa)* — fuentes: de Vaan, LIV. **Status:** atestiguado (latín) + reconstruido (PIE, con variantes →
  distribución).
- **productividad:** alta, en latín y en las lenguas que lo tomaron prestado (es/en/…) como **prefijo culto**.
- **cohorte morfológica:** enlaza a todas las palabras que lo contienen (submarino, subterráneo, subway…) — consulta
  "todas las palabras con sub‑".

## B. Sufijo **‑less**

- **morph_id:** afx·less·SUFFIX·001 · **tipo:** sufijo · **categoría:** **N→Adj** (hope→hopeless)
- **función/sentido:** 'sin, carente de' (fearless, endless, hopeless)
- **esqueleto propio:** código **Λ · Σ** (l→Λ, s→Σ) · núcleo en letras **l · s**
- **genealogía:** ingl. ‑less < AI **‑lēas** < PGmc **\*lausaz** 'suelto, libre, carente' — **cognados:** al. **‑los**
  (furcht‑los = 'sin miedo' = *fearless*!), neer. ‑loos; y **root‑cognado con** ingl. *loose* y *lose*. Fuente: OED,
  Kroonen EDPG.
- **grammaticalización (historia del SENTIDO):** \*lausaz 'suelto/libre' → ‑less 'sin/carente' — un **bleaching**
  semántico de adjetivo pleno a sufijo. El corpus debe registrar esta historia de sentido del afijo.
- **cohorte morfológica:** fearless, hopeless, endless, restless…

---

## C. Cómo se INCLUYE un afijo en el corpus (el modelo)

1. **Un afijo es una ENTRADA (morfema), no solo un span.** Tiene su `morph_id`, su **lineage** (grafo genealógico
   propio: sub‑<lat sub<PIE \*upo; ‑less<OE ‑lēas<PGmc \*lausaz), su **sentido/función** (con su
   grammaticalización), y su **esqueleto propio** (Σ·Φ; Λ·Σ).
2. **Se enlaza a las palabras vía `morph`.** En *submarino*: `morph(role=prefix)→sub‑`, `morph(role=root)→marino`. El
   **núcleo/esqueleto‑core** de submarino **excluye** sub‑ (queda la raíz marino); el **esqueleto de PALABRA** sí lo
   incluye (s·b·…). *(igual que al‑/mi‑ en almohada: fósiles en la palabra, fuera del core)*.
3. **Composición semántica:** el sentido del derivado = f(sentido base, sentido afijo). *fear + ‑less = 'sin miedo'*.
   Es una **arista semántica composicional**, distinta de la polisemia radial de un étimo (cabo, §ejemplo‑cabo).
4. **Cohorte morfológica** = todas las palabras con un afijo dado — una agrupación **queryable** (prima de la cohorte
   de contacto de los arabismos con al‑).
5. **Los afijos tienen sus propias leyes de sonido y su propio esqueleto**, participando en cognacy como cualquier
   morfema (‑less ↔ al. ‑los ↔ *loose/lose*, por Grimm y ablaut).

## D. Relación con ejemplos previos
- **‑less ↔ Angst:** *furchtlos* (al.) = *fearless* (in.) 'sin miedo'; *Furcht* es sinónimo de *Angst*. La cohorte de
  ‑less/‑los toca la red de sentido de FEAR/ANXIETY que abrimos con *Angst*.
- **sub‑ como préstamo culto:** igual que los arabismos, sub‑ entró en español/inglés como material **prestado**
  (del latín) — un afijo puede ser préstamo, con su arista `kind=préstamo`.
- **afijo vs raíz‑y‑patrón:** en almohada el "afijo" era patrón semítico (no concatenativo); aquí sub‑/‑less son
  concatenativos. El modelo `morph.role ∈ {root, affix, pattern}` cubre ambos.

## E. Qué añade al DISEÑO
1. **Afijos = entradas‑morfema de primera clase** con lineage + sentido + grammaticalización + esqueleto propio +
   productividad. Tabla `morph`/`affix` con su propio `ancestry_edge` y su propio `skeleton`.
2. **Doble pertenencia del esqueleto** confirmada: el afijo está en el esqueleto‑PALABRA, fuera del esqueleto‑CORE.
3. **Arista semántica composicional** (base+afijo) como tipo propio, junto a la polisemia radial y la colexificación.
4. **Cohorte morfológica** como agrupación queryable (‑less, sub‑) — hermana de la cohorte de contacto.

⟨ABIERTO⟩ ¿los afijos viven en la tabla `morph` con flag `is_bound`, o en una tabla `affix` propia con su lineage y
skeleton? (afecta cómo consultamos su cohorte y su historia).
