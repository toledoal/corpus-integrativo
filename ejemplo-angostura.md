# Entrada trabajada: **angostura** (español)

Ejemplo completo de una entrada del Corpus Integrativo, capa por capa, para afinar el diseño. Cada afirmación
histórica lleva **fuente**; lo incierto va como **hipótesis/duda con probabilidad**. (v0.1 del ejemplo.)

---

## 0. Identidad de la entrada
- **form_id:** es·angostura·N·001
- **lect:** Español (nivel = lengua) → Ibero-Romance → Romance/Itálico (subsistema) → Indo-Europeo
- **concepto (Concepticon):** NARROWNESS / NARROW_PLACE
- **ortografía:** angostura
- **IPA:** [aŋ.gosˈtu.ɾa]
- **silabación:** an·gos·tu·ra · **acento:** penúltima (‑tu‑) · categoría: sustantivo, femenino
- **fuente:** DLE (RAE); Corominas, *DCECH* s.v. *angosto*

---

## 1. Capa de FORMA (segmentos)

| pos | IPA | fonema norm. | sílaba | rol | ¿acento? | rasgos (resumen) |
|----|-----|------|--------|-----|----|---|
| 1 | a | /a/ | an | núcleo V | no | +bajo,+post? central |
| 2 | ŋ | /n/ | an | coda | — | +nasal (alófono velar ante /g/) |
| 3 | ɡ | /ɡ/ | gos | onset | — | oclusiva, velar, sonora → **clase Χ** |
| 4 | o | /o/ | gos | núcleo V | no | medio, posterior |
| 5 | s | /s/ | gos | coda | — | fricativa, sibilante → **clase Σ** |
| 6 | t | /t/ | tu | onset | — | oclusiva, coronal, sorda → **clase Θ** |
| 7 | u | /u/ | tu | núcleo V | **sí** | alto, posterior |
| 8 | ɾ | /ɾ/ | ra | onset | — | vibrante simple, líquida → **clase Λ** |
| 9 | a | /a/ | ra | núcleo V | no | central/bajo |

**Análisis vocálico:** secuencia a‑o‑u‑a; acento en /u/. (Nota: la /ŋ/ es alófono velar de /n/ → se normaliza a /n/.)

---

## 2. Capa MORFOLÓGICA
- **angost‑** = raíz (adjetivo *angosto* 'estrecho')
- **‑ura** = sufijo derivativo (nominalizador abstracto: cf. *amargura, hermosura, dulzura*), del latín **‑ūra**
- estructura: `[angost]_raíz + [ura]_sufijo`

---

## 3. Capa ENDOLINGÜÍSTICA — esqueleto consonántico *(el objeto que sí usamos hoy)*
- **esqueleto de la PALABRA** (todas las consonantes, sin vocales): `n · ɡ · s · t · ɾ`
  - código canónico (símbolos de clase): **Ξ · Χ · Σ · Θ · Λ**
- **esqueleto del NÚCLEO/raíz** (angost‑, sin sufijo ‑ura): `n · ɡ · s · t`
  - código canónico: **Ξ · Χ · Σ · Θ**
- **skeleton_id:** SK·es·angost·001 (raíz) — enlazable por ID a otras entradas con el mismo esqueleto/código
- maquinaria: `src/build_skeltree.py`, `src/gi/skeletons.py`, `src/cc/skeletons.py`

---

## 4. Capa CRIPTOLÓGICA — la palabra como objeto matemático (montada sobre el esqueleto)
- **monádico** (en la entrada): vectores F₂ⁿ de {n,ɡ,s,t,ɾ}; longitud de esqueleto = 4 (núcleo) / 5 (palabra);
  medida info‑teórica intrínseca (sorpresa del esqueleto dado el inventario del español) — *(⟨ABIERTO⟩ ¿desde Fase 0?)*
- **diádico** (aristas, §6 y capa 6): operadores hacia cognados/ancestros — ver capa 6.
- **sistémico** (referencia): kernel K_{latín→español} propiedad del par de lects.

---

## 5. Capa GENEALÓGICA — "toda la historia de la palabra" (grafo probabilístico)

Escalera hacia atrás (cada arista: kind · prob · status · fuente):

| nivel | forma | arista al padre | status | fuente |
|---|---|---|---|---|
| lengua (es) | **angostura** | ← deriv. interna de *angosto* + ‑ura | atestiguado | Corominas DCECH |
| — (alt.) | (¿VLat \***angustūra**?) | ← herencia | **dudoso** (prob ≈ 0.3) | hipótesis; poca atestiguación |
| lengua ant. | latín **angustus** 'estrecho' (adj.) → esp. *angosto* | herencia · prob 0.97 | atestiguado | de Vaan *EDL* s.v. *angustus* |
| proto‑rama | proto‑itálico \*angos‑to‑ / \*anɣosto‑ | reconstruido · prob 0.8 | reconstruido | de Vaan; LIV² |
| **PIE (plural)** | \***h₂enǵʰ‑** 'estrecho, apretar' | reconstruido | reconstruido | **ver 5a** |

### 5a. PIE plural (varias reconstrucciones, integradas por distribución)
| variante | escuela/fuente | nota | prob (distrib.) |
|---|---|---|---|
| \*h₂enǵʰ‑ | LIV² (Rix) | raíz verbal 'apretar/estrechar' | 0.55 |
| \*h₂emǵʰ‑ (con m) | Pokorny / lecturas antiguas | nasal labial | 0.25 |
| \*h₂enǵʰ‑ + s‑stem \*h₂énǵʰ‑os‑ | de Vaan (angustus < \*angos‑to‑) | vía neutro en ‑os‑ | 0.20 |

*(La probabilidad sale de la distribución sobre variantes ponderada por respaldo/citación, no de elegir una. Todas se
guardan con su fuente.)*

### 5b. Sustrato
- **ninguno relevante**: *angostura* es herencia latina limpia. (El campo `substrate_edge` queda vacío aquí — pero
  existe para casos como *lanza*.) prob(sustrato) ≈ 0.

### 5c. Futuro
- extensión a nostrático u otras macroconstrucciones: **abierta**, hoy sin arista.

---

## 6. Red de CORRESPONDENCIAS / operadores (diádico — aristas entre entradas)

**Latín *angustus* → español *angosto*** (raíz; el sufijo ‑ura es innovación romance, se compara la raíz):

| segmento | latín | español | operador |
|---|---|---|---|
| C1 | n | n | Δ = ∅ (idéntico) |
| C2 | g | ɡ | Δ = ∅ |
| C3 | s | s | Δ = ∅ |
| C4 | t | t | Δ = ∅ |
| V | ŭ | o | (vocálico) ŭ→o — regular esp. |
| desin. | ‑us | ‑o | morfológico |

**Hallazgo que ilustra el proyecto:** el **esqueleto consonántico se CONSERVA** (Ξ·Χ·Σ·Θ idéntico latín→español); el
cambio vive en la **vocal** (ŭ→o) y la **desinencia**. Es decir, el "cifrado" sobre consonantes aquí es casi la
identidad — exactamente el tipo de invariante que el corpus debe hacer visible.

*(Aristas adicionales del mismo conjunto cognado en la capa 7.)*

---

## 7. Conjunto COGNADO (red de la FORMA, entre lenguas) — familia \*h₂enǵʰ‑

| lengua | forma | glosa | vía |
|---|---|---|---|
| latín | angustus / angere / angustia / anxius / angīna | estrecho / apretar / angustia / ansioso / angina | herencia |
| italiano | angusto | estrecho | herencia |
| francés | angoisse | angustia | < lat. *angustia* |
| inglés | anguish, anxious, angina; **anger** | angustia… / enojo | vía fr./nórdico |
| alemán | **eng**; **Angst** | estrecho; angustia/miedo | herencia germánica |
| griego | ἄγχω *ánkhō*, ἄγχι *ánkhi* | estrangular; cerca | herencia |
| sánscrito | aṃhú‑; áṃhas‑ | estrecho; congoja | herencia |
| avéstico | ązah‑ | congoja | herencia |

*(cognados por RAÍZ; muchos no comparten la derivación ‑ura, pero sí el étimo. Fuente: de Vaan, Kroonen, LIV².)*

---

## 8. Red POLISÉMICA (red del SENTIDO, dentro del español — NO requiere cognación)

**Sentidos de *angostura*** (en contexto):
1. estrechez (cualidad de angosto)
2. paso/lugar estrecho; estrecho de un río o montaña
3. [topónimo] Angostura (hoy Ciudad Bolívar, Venezuela)
4. [metonimia] amargo de Angostura (bíter)

**Enlaces polisémicos / sinónimos (NO cognados con *angostura*):**
- estrechez, estrecho, desfiladero, **garganta** (¡colexifica garganta‑del‑cuerpo + garganta‑paso!), cañón, paso
- **antónimo:** *anchura* (gemelo morfológico ancho+‑ura, pero raíz distinta: *ancho* < lat. *amplus*)

**Colexificaciones registradas:** angostura {estrechez ↔ estrecho‑geográfico}; garganta {throat ↔ gorge}.

*(Estos enlaces construyen la red polisemántica del español; ninguno exige ser cognado — es la cara del significado.)*

---

## 9. FUENTES citadas
- RAE, *Diccionario de la lengua española* (s.v. angostura, angosto, anchura).
- Corominas & Pascual, *Diccionario Crítico Etimológico Castellano e Hispánico* (s.v. angosto).
- de Vaan, *Etymological Dictionary of Latin and the other Italic Languages* (s.v. angustus, angō).
- Rix et al., *Lexikon der indogermanischen Verben* (LIV²) (\*h₂enǵʰ‑).
- Kroonen, *Etymological Dictionary of Proto‑Germanic* (eng, angst).
- Pokorny, *IEW* (variante con m).

---

## 10. Qué nos ENSEÑA este ejemplo sobre el diseño de la entrada

1. **La entrada no es una fila: es un nodo con capas y aristas.** angostura toca: 1 form + 9 segments + 1 skeleton +
   1 crypto + N aristas genealógicas + M miembros cognados + K enlaces polisémicos. El esquema debe modelar esto como
   grafo, no como tabla plana. *(refuerza Postgres + AGE)*
2. **Raíz vs palabra importa de verdad.** El esqueleto del núcleo (n‑ɡ‑s‑t) es lo que empareja con los cognados; el de
   la palabra (con ‑ɡ‑s‑t‑ɾ) incluye el sufijo. Guardar **ambos** (como decidiste) es correcto y necesario.
3. **La conservación del esqueleto es un hallazgo de primera clase.** latín→español conserva Ξ·Χ·Σ·Θ y cambia solo la
   vocal/desinencia. El corpus debe poder **consultar "esqueletos conservados a través del linaje"** directamente.
4. **La probabilidad y la duda son ubicuas, no excepcionales.** Ya en una palabra "fácil" aparecen: VLat *angustūra
   (dudoso), tres PIE en competencia (distribución), sustrato (vacío pero evaluado). El esquema `ancestry_edge` +
   `protoform_hypothesis` con prob+status+fuente los absorbe bien.
5. **Cognación y polisemia son ejes ortogonales.** *anchura* es antónimo y gemelo morfológico pero NO cognado;
   *garganta* es sinónimo geográfico pero NO cognado. La red polisémica captura lo que la genealógica no debe.
6. **Falta la capa que no tenemos: prosodia.** Aquí el acento (‑tu‑) sí lo sé del español moderno, pero para estadios
   antiguos/otras lenguas será el hueco (§4 del PLAN).

⟨ABIERTO⟩ ¿el diseño de entrada te sirve así? ¿qué capa quieres más rica o más simple? ¿el código canónico en
símbolos de clase (Ξ·Χ·Σ·Θ) o en letras (n·k·s·t)?
