# Derechos de uso / extracción de datos — para armar NUESTRA propia BD

Debida diligencia (ago‑2026). Vamos a **extraer** datos de fuentes externas y construir una **base de datos propia**
que probablemente **redistribuyamos**. Esto define qué podemos hacer con cada fuente. *(No es asesoría legal; para uso
comercial o dudas serias, confirmar con el archivo de licencia de cada dataset y con un abogado.)*

---

## 0. El principio legal (dos capas)

1. **Los HECHOS no tienen copyright.** "Tal palabra significa X, su IPA es Y, desciende de Z" son hechos → libres.
   **PERO** dos cosas sí están protegidas:
   - La **EXPRESIÓN**: el *texto redactado* (prosa de etimología, definiciones) de una fuente. En Kaikki, los campos
     `ety` (etimología en prosa) y `gloss` (definiciones) **son autoría de Wiktionary** → CC BY‑SA.
   - El **derecho *sui generis* de BASE DE DATOS** (UE): extraer "partes sustanciales" de una BD protegida puede
     requerir permiso **aunque sean hechos**. La licencia CC de la fuente es justamente lo que nos da ese permiso.
2. **Nuestras capas COMPUTADAS son creación nuestra** (skeltree recomputado, códigos, objeto criptológico, operadores)
   → las poseemos. *(Pero si se computan A PARTIR de datos CC BY‑SA, son obra derivada → hereda ShareAlike.)*
3. **La atribución es obligatoria en TODAS** (CC BY y CC BY‑SA). → nuestra tabla **`source` obligatoria** ya es el
   mecanismo de cumplimiento. Buen diseño, ahora también por ley.

---

## 1. Clasificación de fuentes por licencia (verificado)

### 🟢 PERMISIVAS — CC BY 4.0 (extraer + redistribuir con atribución; compatibles con BY‑SA)
- **Glottolog** (CC BY 4.0) · **Concepticon** (CC BY 4.0) · **CLTS** · **CLICS³** · **WOLD** · **WALS** · **Grambank**
  · **ASJP** · **IE‑CoR (iecor)** · **IDS** · la mayoría de datasets **Lexibank** *(algunos componentes varían —
  revisar per‑dataset)*.
- **WordNet (Princeton)** — licencia WordNet (tipo BSD/permisiva).

### 🟡 COPYLEFT — CC BY‑SA (extraer + redistribuir, PERO el derivado debe ser ShareAlike)
- **Kaikki / Wiktextract (Wiktionary)** = **CC BY‑SA 3.0 + GFDL** — **nuestra fuente PRIMARIA.** ✅ verificado.
- **LIV²** (nuestra digitalización LiLa) = **CC BY‑SA 4.0.** ✅ (README local).
- **NorthEuraLex** = **CC BY‑SA 4.0.** ✅ verificado.
- **PHOIBLE** = **CC BY‑SA 3.0.** ✅ verificado.
- **UniMorph** = CC BY‑SA (parte de Wiktionary) — revisar.

### 🔴 RESTRINGIDAS — NO ingerir a la BD redistribuible (solo consulta local / requieren permiso)
- **StressTyp2** = **CC BY‑NC‑ND 4.0** ✅ verificado. **NC** (no comercial) **+ ND (sin derivados)** → **no podemos
  extraerlo** a una BD derivada. ⚠️ *(golpe a la capa de acento — hay que sacar el acento de otras fuentes.)*
- **BabelNet** = **CC BY‑NC‑SA 3.0 + licencia de investigación** (no comercial). ✅ verificado. → cuarentena.
- **UD (Universal Dependencies)** — licencia **por treebank** (algunos NC/NC‑SA) → revisar cada uno.
- **OMW (Open Multilingual WordNet)** — **por wordnet de cada lengua** (algunos restrictivos) → revisar.
- **StarLing / Tower of Babel** (Starostin, nostrático) — términos poco claros → tratar como **referencia‑con‑fuente**,
  probablemente no redistribuible; **verificar**.
- **Pokorny IEW / digitalizaciones de impresos** — el impreso original tiene copyright; las digitalizaciones varían →
  **verificar por fuente**.
- **DatSemShift** — **verificar** en datsemshift.ru (probable: uso académico + atribución).

---

## 2. Consecuencia para NUESTRA licencia

Como la **fuente primaria (Kaikki)** y varias clave (**LIV², NorthEuraLex, PHOIBLE**) son **CC BY‑SA**, y vamos a
redistribuir su contenido:

> **La BD redistribuible debe ser CC BY‑SA 4.0.** Las fuentes CC BY (🟢) se integran limpiamente (BY es compatible
> hacia BY‑SA). Es el mínimo común denominador y el camino honesto y simple.

**Alternativa** (si algún día quisiéramos una licencia más permisiva/propietaria): **no** redistribuir el contenido
CC BY‑SA verbatim; almacenar solo **hechos no‑copyrightables + nuestras computaciones + enlaces de vuelta a la
fuente**. Es más frágil legalmente y se pierde la prosa etimológica. Para este proyecto, **CC BY‑SA es lo recomendado.**

---

## 3. Arquitectura de la BD por licencia (capas + cuarentena)

- **Capa CC BY‑SA (redistribuible):** Kaikki + LIV² + NorthEuraLex + PHOIBLE + todas las 🟢 CC BY plegadas.
- **Capa PROPIA (nuestra):** skeltree recomputado, códigos, objeto criptológico, operadores → CC BY‑SA (coherente;
  además derivadas de BY‑SA lo heredan).
- **Cuarentena (uso local, NO redistribuir):** StressTyp2 (ND), BabelNet (NC), UD/OMW no‑libres, StarLing y Pokorny
  hasta verificar. Se pueden **consultar** para investigación, pero no se hornean en la BD que publicamos.

**Cada dato lleva `source_id`** → atribución automática (cumplimiento CC) y trazabilidad académica en el mismo gesto.

---

## 4. Efecto en las capas del corpus (qué se resiente)
- **Forma / etimología / morfología / protos:** 🟢🟡 abundante (Kaikki, LIV², CLDF). Sin problema.
- **Semántica / polisemia / colexificación:** CLICS³ (🟢) + WordNet (🟢) OK; **BabelNet queda fuera** (NC).
- **Acento / prosodia:** **la fuente directa principal (StressTyp2) queda FUERA por ND.** → sacar el acento de:
  (a) **corpus antiguos con acento marcado** (Rigveda védico, griego politónico, lituano — muchos textos antiguos son
  de **dominio público**), (b) **diccionarios/Kaikki** donde el IPA trae acento, (c) **PHOIBLE** (🟡) para tono. Es
  más trabajo pero legalmente limpio.
- **Genealogía/árbol:** Glottolog (🟢) OK.

---

## 5. Acciones
1. Fijar la licencia del corpus = **CC BY‑SA 4.0** (salvo que decidas la vía "solo‑hechos").
2. Implementar la **cuarentena** (tabla/flag `redistributable` por `source`): StressTyp2, BabelNet, UD/OMW no‑libres,
   StarLing, Pokorny → `redistributable=false`.
3. **Verificar** directamente: DatSemShift, StarLing, Pokorny‑digital, licencias per‑dataset de Lexibank, per‑treebank
   de UD, per‑wordnet de OMW.
4. `source(id, citation, url, license, redistributable)` — añadir `license` y `redistributable` al esquema (§5 PLAN).

⟨ABIERTO⟩ ¿confirmas **CC BY‑SA 4.0** para nuestra BD? ¿O prefieres explorar la vía "solo‑hechos + enlaces" para
mantener opción de licencia más libre?
