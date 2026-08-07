# Estado del Corpus vs PLAN — revisión (2026-08-06)

Contraste del PLAN.md (v0.3) con lo que hay en la BD. Norte: **corpus completo, lleno de lenguas relacionadas y
curadas, con TODAS las capas** (§3f "toda la historia de la palabra"). NO experimentos.

**Escala actual:** 12 familias IE completas · ~2.06M formas · 556 lenguas · 6 fuentes coexistiendo
(kaikki, ids, nel, iecor, lexibank, liv) · QA 27 OK / 0.

## Capas del PLAN §1 — cobertura

| Capa | PLAN | Estado | Nota |
|---|---|---|---|
| **Forma** (IPA+ortografía) | §1 | ✅ | ortografía 100%; IPA fuente 80% + G2P elaborada |
| **Segmentos** | §1 | ✅ | segments_raw/norm + tabla segment |
| **Fonología: rasgos/sílaba** | §1/§6b | ◐ | rasgos F₂ⁿ por fonema (feature) ✅; sílaba parcial |
| **Prosodia / acento / tono** | §4 | ○ | **slots vacíos** — aplazado en el PLAN (sin fuente); el mayor hueco de capa |
| **Morfología** (raíz/afijos) | §1/§6h | ◐ | 44% con morfemas; raíz (core) 46%; afijos NO son entrada-morfema de 1ª clase aún |
| **Semántica: sentidos** | §1 | ✅ | 96% con glosa |
| **Concepto (Concepticon)** | §1/red 3 | ◐ | **39%** (ids/nel/iecor/lexibank + kaikki por glosa); falta el grueso de Kaikki |
| **Polisemia intra-lengua** | red 2 | ✅ | polyseme_link |
| **Colexificación** | red 2/3 | ✅ | **138k** cross-lingüística (validada vs CLICS) |
| **Cognados (red forma)** | red 1 | ✅ | 3 redes: kaikki-cog, kaikki-etymology, iecor-oro |
| **Genealogía / linaje** | §3 | ◐ | 1.25M aristas; **PIE-reach 150k** (ver abajo) |
| **Contacto / préstamos** | §1 | ◐ | is_loan marcado (186k); cohorte de contacto parcial |
| **Sustrato** | §3d | ○ | substrate_edge existe, **casi vacío** — falta WOLD + literatura |
| **Esqueleto consonántico + código** | §6e | ✅ | palabra + núcleo (raíz), por-estadio; OAS aplazado (correcto) |
| **Criptológico (self-info)** | §6a | ◐ | crypto.self_info ✅; operadores Δ/T diádicos parciales |

## Genealogía §3 — el corazón (detalle)

- **Grafo hijo→padre con kind/status/fuente** ✅ (`form_etymology`, `ancestry_edge`).
- **PIE plural / reconstrucciones en competencia** ◐ — hay Kaikki + LIV² sobre el mismo set, pero la
  **probabilidad NO es por distribución citada** (§3f DECIDIDO): hoy son pesos fijos (LIV 0.9, kaikki 0.5). Falta la
  distribución ponderada por respaldo/citación.
- **Linaje hasta PIE** — subió de 41k → **150.175 formas** esta sesión (recarga de protos con etimología, carga de
  protos intermedios gmw-pro/cel-pro/iir-pro/ine-bsl-pro, parser de árbol/cadena, iecor root_forms, encadenado
  resolve_lineage). Honesto por antigüedad: Sánscrito 78%, Lituano 50%, Latín 43%, modernas ~18-24%. **Techo real:**
  mucho léxico no tiene étimo PIE documentado; subir requiere **Pokorny (CLDF, público)** o de Vaan/Kroonen (copyright).
- **Vista "toda la historia"** ✅ en el visor (cadena completa + "llega a PIE ✓").
- **Sustratos por probabilidad** ○ — pendiente (WOLD + literatura de sustrato).
- **Extensión nostrática** ○ — futuro.

## Qué FALTA para el corpus completo (prioridad)

**A. Densidad de léxicos y listas (lo que señalaste):**
1. Cargar MÁS datasets Lexibank (hoy solo 19k formas lexibank; hay cientos de datasets CLDF) → densidad por lengua.
2. Completar concepto Kaikki→Concepticon (39%→más) con glosas definicionales.
3. Más lenguas: dialectos, y no-IE (Urálico, Túrquico, Semítico…) hacia "todas las lenguas".

**B. Profundizar el linaje a PIE (tu foco):**
4. **Pokorny IEW (CLDF)** — diccionario etimológico PIE público, descargable → sube Latín/Germánico/etc.→PIE.
5. Cargar Proto-Iranian / Proto-Indo-Aryan (no hay extracto Kaikki; vía dump crudo).
6. Normalizar códigos de proto duplicados (bsl-pro/bsw-pro/ine-bsl-pro ya unificado; revisar toc-pro/ine-toc-pro).

**C. Capas ausentes del PLAN:**
7. **Prosodia/acento/tono** — subtarea de investigación (fuentes con acento); de aquí cuelga el endorritmo.
8. **Sustratos** (substrate_edge) — WOLD + literatura, con probabilidad y duda.
9. **Probabilidad por distribución citada** para reconstrucciones en competencia (§3f).
10. **Afijos como entrada-morfema de 1ª clase** (§6h): lineage + esqueleto + productividad propios.

**D. Fusión y calidad:**
11. Vincular fuentes por glottocode (iecor iec_* ↔ kaikki) para que la cognación oro enriquezca la red principal.
12. Auditoría de nombres de lect (varios con name=código); dedup de aristas form_etymology.
13. Versionado del corpus (§9.2, abierto).

## Veredicto
El esqueleto multi-capa/multi-fuente del PLAN **está en pie y curado** (formas, sentidos, cognados×3, colexificación,
linaje con "toda la historia", esqueleto). Lo que más falta para "completo": **densidad de léxicos** (más Lexibank +
concepto Kaikki), **profundizar PIE** (Pokorny), y las **capas aplazadas** (prosodia, sustrato, probabilidad por
distribución). Ninguna requiere experimentos: es carga, curación y fuentes.
