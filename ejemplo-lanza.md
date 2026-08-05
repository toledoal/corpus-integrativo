# Entrada trabajada: **lanza** (español) — el caso de SUSTRATO DUDOSO

Cuarto ejemplo, el que Alejandro señaló para estresar la **duda de sustrato**. Bonus: *lanza* **cambia el esqueleto**
por palatalización (contraste con *angostura*, que lo conserva) y reengancha con la /k/‑palatalización de los papers.

---

## 0. Identidad
- **form_id:** es·lanza·N·001 · **lect:** Español → Ibero‑Romance → Romance/Itálico → Indo‑Europeo
- **concepto:** SPEAR / LANCE · **IPA:** [ˈlan.θa] (o [ˈlan.sa] seseante) · acento: penúltima
- **fuente:** DLE; Corominas *DCECH* s.v. *lanza*

## 1–2. Forma y morfología (breve)
- segmentos: l·a·n·θ·a → consonantes **l, n, θ** · monomorfémica (sin sufijo derivativo aquí)

## 3. Esqueleto consonántico — **CAMBIA** de latín a español
- **lanza (es):** `l · n · θ` → **Λ · Ξ · Θ**
- **lancea (lat) [lankea]:** `l · n · k` → **Λ · Ξ · Χ**
- **⚠️ el esqueleto NO se conserva:** `Χ(k) → Θ(θ)` — la velar se vuelve coronal. **Contraste directo con angostura**
  (Ξ·Χ·Σ·Θ idéntico lat→esp): allí el esqueleto era invariante; aquí la **palatalización lo muta**.

## 4. Cripto / operador — es la MISMA ley de los papers
- operador dirigido lat→esp: **`k → θ | _V[frontal]`** (la /c/ latina ante /e/ de *lancea* → /θ/).
- Es exactamente la palatalización románica de /k/ ante vocal frontal que **recuperamos dirigidamente** en el trabajo
  de transformations (Latín /k/, p=0.0002). *lanza* es un caso vivo de ese operador cambiando el esqueleto.

## 5. Genealogía — ⭐ el SUSTRATO como DUDA de primera clase

| nivel | forma | arista | status | prob | fuente |
|---|---|---|---|---|---|
| lengua (es) | **lanza** | ← herencia | atestiguado | 0.98 | DLE, Corominas |
| lengua ant. | latín **lancea** 'lanza ligera' | ← herencia | atestiguado | 0.98 | de Vaan |
| **origen de *lancea*** | ⟨préstamo de **celtíbero/hispano‑celta** \*lankia?⟩ | **préstamo/sustrato** | **DUDOSO** | ~0.5 | testimonio antiguo (Varrón/Gelio: voz *hispana*); et. celta |
| — (alt.) | ⟨voz **ibérica**?⟩ | préstamo/sustrato | **DUDOSO** | ~0.25 | hipótesis alternativa |
| — (alt.) | ⟨herencia IE directa?⟩ | herencia | **DUDOSO** | ~0.25 | minoritaria |

**Cómo se maneja la duda (idea.md):** *lancea* es casi seguramente un **préstamo de sustrato** hispano en latín,
pero **el donante exacto y la forma no están atestiguados** → se guardan **todas** las hipótesis (celtíbero/ibérico/
herencia) con **probabilidad por distribución** y **status=dudoso**, cada una con su fuente/argumento. No se borra ni
se afirma una sola. El campo `substrate_edge` aquí SÍ se puebla (a diferencia de angostura/Angst).

## 6–7. Redes
- **Cognados (forma):** difícil por el origen dudoso — si es celta, la familia es la raíz celta; si es IE, otra. Se
  deja **abierto/condicionado a la hipótesis** (¡el corpus debe soportar cognacy *condicional a una rama del grafo de
  duda*!).
- **Polisemia (español):** sentidos: arma; (lanza de carruaje) timón/pértiga; *romper una lanza por* (locución).
  Sinónimos NO cognados: *pica, venablo, jabalina, asta*.

## 8. Qué añade al DISEÑO
1. **La duda de sustrato es multi‑hipótesis con distribución de probabilidad** — celtíbero vs ibérico vs herencia,
   todas guardadas con fuente; ninguna elegida. `substrate_edge`/`ancestry_edge` con `status=dudoso` + prob.
2. **La cognación puede ser CONDICIONAL a una hipótesis genealógica.** Si el origen es dudoso, "sus cognados" dependen
   de qué rama del grafo de duda tomes → el corpus necesita cognacy **condicionada** a un camino del grafo.
3. **El esqueleto NO siempre se conserva:** aquí la palatalización lo muta (Χ→Θ). El corpus debe distinguir
   correspondencias **conservadoras** (angostura) de **transformadoras** (lanza) — y la transformación *es* la ley.
4. Reengancha con transformations: el operador k→θ|frontal es el hallazgo dirigido de los papers, ahora **por entrada**.
