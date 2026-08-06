# Experimento — la regla biclase, medida contra la genealogía

*El documento `oas-segmentos-biclase` propone que ciertos segmentos IPA (ʃ ʒ ɲ ŋ ʎ…) aporten DOS clases OAS al
esqueleto (Σ·Χ, Ξ·Χ, Λ·Χ), y predice (§6) que eso AUMENTA la conservación del código entre coderivados. Lo
implementamos, lo corrimos, y lo medimos. Resultado: a nivel corpus, la predicción no se sostiene.*

## Qué se implementó

- Regla biclase por destino articulatorio: ʃ ʒ ʂ ʐ ɕ ʑ → Σ·Χ; ɳ ɲ ŋ ɴ → Ξ·Χ; ʎ → Λ·Χ. Orden base·Χ (§9).
- Africadas tʃ dʒ **no** biclase → Σ (transición Θ→Σ, por destino). *(Esto además corrigió un bug previo: la
  tʃ con tie-bar se clasificaba como Θ por su primer carácter; ahora es Σ. Se conserva.)*
- **Guarda de asimilación**: un dorsal-nasal cuya coloración Χ es adyacente a un consonante Χ siguiente
  (ŋ+g en *banco*, *angustus*) es /n/ asimilada, no ŋ fonémica → se lee solo la base. La ŋ que absorbió el
  velar (*sing*, sin velar siguiente) sí es biclase. Sin esta guarda, *angustus* daba Ξ·Χ·**Χ**·Σ·Θ·Σ (dorso
  duplicado) — la primera señal de que la regla a ciegas sobre-genera.
- El IPA original se conserva siempre en `form.segments_raw` (trazabilidad C0★★): nada irreversible.

## La medición (`analysis/biclass_conservation.py`)

Métrica: dentro de cada `cognate_set`, cobertura del código MODAL = miembros con el código más común / total.
Promedio por familia, con biclase y sin. Δ>0 = biclase conserva mejor.

| Familia | Sets | Conservación SIN | CON biclase | Δ |
|---|---|---|---|---|
| Germánico | 17.571 | 0.839 | 0.836 | **−0.003** |
| Itálico | 532 | 0.710 | 0.710 | 0.000 |
| Romance | 15.717 | 0.685 | 0.674 | **−0.011** |
| Eslavo | 6.916 | 0.856 | 0.843 | **−0.012** |

**La biclase a ciegas REDUCE la conservación en todas las familias** — lo contrario del §6.

## Por qué

El §6 acierta para el subconjunto *estrecho* de coderivados que cruzan la frontera racimo↔segmento
(`sk↔ʃ`: *shall*=*skal*=Σ·Χ·Λ). Pero promediado sobre **todos** los coderivados, la mayoría no cruza esa
frontera: cuando un miembro tiene ʃ (→Σ·Χ) y sus coderivados tienen s, ʃ o x, la Χ extra lo **desalinea** de
la mayoría más de lo que lo alinea. El caso eslavo que anticipó Alejandro es el más claro: la *š* del RUKI
viene de `*s` (no de `*sk`), y leerla Σ·Χ le añade una Χ que sus coderivados no tienen → se pierde el enlace.

## Decisión

**Revertido a no-biclase por defecto** (`compute(.., biclass=False)`) — conserva mejor, medido. Se mantiene
toda la maquinaria (regla, guarda, flag `biclass=True`, medidor) para una versión futura **condicionada a la
genealogía**: aplicar Σ·Χ/Ξ·Χ/Λ·Χ SOLO cuando el etymon evidencia racimo/origen dorsal, no por la superficie.
Esa es la lectura fiel al criterio diacrónico del propio documento (§2), y la única que no rompe coderivados.

## Lección

La biclase articulatoria es correcta como *descripción* del segmento, pero como *regla de esqueleto* debe
condicionarse a la historia, no a la superficie. Medir contra la genealogía —no asumir— es lo que lo reveló;
el mismo principio que arbitra el campo semántico arbitra aquí el mapeo IPA→clase.
