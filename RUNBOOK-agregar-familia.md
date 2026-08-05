# Runbook — agregar una familia o rama lingüística

Procedimiento ordenado para incorporar un nuevo subsistema (Germánico, Eslavo, Céltico, no-IE…) sin
pisar lo ya cargado. El pipeline está **parametrizado por familia** (`CI_FAMILY`) y todos los borrados
están **acotados** a la familia/lengua, así que las familias **coexisten**.

## 1. Declarar la familia (`ingest/families.py`)

Añade una entrada a `FAMILIES` con:

- **`members`** — los códigos de lect del subsistema (los únicos que el pipeline toca para esta familia).
- **`ancestors`** — niveles de ancestro por prioridad, cada uno `(etiqueta, [lects-padre], status)` con
  `status ∈ {atestiguado, reconstruido}`. **Incluye aquí los PROTO-lenguajes** (proto-rama, PIE…). El
  primer lect de cada nivel es la clave canónica; variantes de una misma lengua (p. ej. estadios de latín)
  van juntas en un nivel para no fragmentar la cognación.
- **`kaikki_files`** — `NombreDeArchivo.jsonl → código`. Incluye los protos si tienes su dump.
- **`all_load`** — archivos que se cargan con `--all` (protos y lenguas antiguas **sin etimología**: su
  valor es la FORMA reconstruida, no su historia).
- **`reconcile_pairs`** — `glottocode → ISO` para fusionar nodos-lengua duplicados (Lexibank vs Kaikki).

## 2. Conseguir los datos

Descarga de kaikki.org los `.jsonl` que falten a `$CI_KAIKKI_DIR` (default `../data/lexicon/kaikki/dict`).
No todos existen como dump (p. ej. Osco/Falisco dan 404) — esos se quedan como ancestros etimológicos.

## 3. Cargar y construir (un comando)

```bash
./ingest/add_family.sh germanic
```

Hace, en orden: cargar normales → cargar protos/antiguas con `--all` → segmentar IPA → esqueleto →
esqueleto ortográfico (para las sin IPA) → afijos → core → reconciliar lects/formas → marcar calidad →
capas analíticas de la familia → QA. Todo acotado: no toca otras familias.

## 4. Verificar

La QA corre al final (`OK=… ❌=0`). Los guardarraíles comprueban que ningún lect ajeno se coló y que
cada fila analítica usa lects declarados de su familia. Revisa además un caso conocido de resonancia
entre ramas (código de esqueleto compartido) para sanity-check.

## Al salir del indoeuropeo (no-IE)

Antes de cargar familias tipológicamente distintas, revisar el objeto OAS/esqueleto:

- **Inventario fonético**: clicks, implosivas, retroflejas, faringales → mapeo IPA→clase (ver
  `recompute_skeleton.SKEL_NORM` y el dict de clases). Puede requerir extender las clases.
- **Tono**: capturado en `segment.tone`/`length`; explotarlo requiere fuentes con tono (PHOIBLE).
- **Morfología no concatenativa** (semítico raíz-y-patrón): el esqueleto consonántico ya modela la raíz,
  pero `core_skeleton` (pelado de afijos) asume concatenación → revisar.
- **Cognación/genealogía**: fuera del IE la etimología de Kaikki es más rala; considerar fuentes CLDF por
  familia vía `cldf_ingest.py`.

Documenta en `REPORTE.md` qué NO captura el corpus para esa familia (principio: declarar los huecos).
