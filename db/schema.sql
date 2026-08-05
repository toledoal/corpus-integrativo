-- ============================================================================
-- Corpus Integrativo · esquema v0.3 (Fase 0)  ·  PostgreSQL
-- Implementa PLAN.md §5 + los 7 ejemplos trabajados. Licencia de la BD: CC BY-SA 4.0.
-- Cargar:  psql -d corpus_integrativo -f db/schema.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Vocabularios controlados (ENUM)
-- ----------------------------------------------------------------------------
CREATE TYPE lect_level    AS ENUM ('idiolecto','dialecto','lengua','subfamilia','proto_rama','pie','nostratico');
CREATE TYPE edge_kind     AS ENUM ('herencia','prestamo','sustrato','reconstruido');
CREATE TYPE edge_status   AS ENUM ('atestiguado','reconstruido','dudoso');
CREATE TYPE corr_type     AS ENUM ('conservar','mutar','truncar');   -- correspondencia de esqueleto
CREATE TYPE morph_role    AS ENUM ('root','affix','pattern');        -- concatenativo y raíz-y-patrón
CREATE TYPE affix_type    AS ENUM ('prefix','suffix','infix','pattern');

-- ----------------------------------------------------------------------------
-- Fuentes (atribución obligatoria = cumplimiento CC; license/redistributable = cuarentena)
-- ----------------------------------------------------------------------------
CREATE TABLE source (
    id             TEXT PRIMARY KEY,
    citation       TEXT NOT NULL,
    url            TEXT,
    kind           TEXT,                       -- diccionario, corpus, reconstrucción, tipológica…
    license        TEXT,                       -- 'CC-BY-4.0','CC-BY-SA-4.0','CC-BY-NC-ND-4.0'…
    redistributable BOOLEAN NOT NULL DEFAULT TRUE  -- FALSE = cuarentena (NC/ND), no se publica
);

-- ----------------------------------------------------------------------------
-- Conceptos (nodo Concepticon = red del SENTIDO entre lenguas)
-- ----------------------------------------------------------------------------
CREATE TABLE concept (
    id            SERIAL PRIMARY KEY,
    concepticon_id TEXT UNIQUE,                  -- ID Concepticon (glue cross-dataset/cross-lengua)
    concepticon_gloss TEXT,                      -- p.ej. 'NARROW','FEAR (BE AFRAID)'
    gloss_en      TEXT,
    gloss_de      TEXT,                          -- ancla alemana (desambiguación)
    semantic_field TEXT,                         -- 'The physical world', 'Emotions and values'…
    ontological_category TEXT,                   -- 'Person/Thing','Property','Action/Process'…
    definition    TEXT,                          -- definición Concepticon
    validated     BOOLEAN                        -- concepticon_validated
);

-- ----------------------------------------------------------------------------
-- Lects (escalera de niveles) + grafo de linaje probabilístico
-- ----------------------------------------------------------------------------
CREATE TABLE lect (
    id            TEXT PRIMARY KEY,             -- 'es','la','vsn','got','proto-italic','pie-liv'…
    name          TEXT NOT NULL,
    level         lect_level NOT NULL,
    glottocode    TEXT,                         -- enlace a Glottolog (árbol/clasificación)
    iso639        TEXT,
    macrosystem   TEXT,                         -- GENEALÓGICO: 'indo-europeo','semitico'… (del LECT; el del origen va en la arista)
    family        TEXT,                         -- familia (de Glottolog/Lexibank)
    subgroup      TEXT,                         -- sub-rama
    macroarea     TEXT,                         -- GEOGRÁFICO: 'Eurasia','Africa','South America'… (Glottolog/Lexibank)
    latitude      NUMERIC(8,4),                 -- geo (para hipótesis de geografía del cambio)
    longitude     NUMERIC(8,4),
    date_lo       INTEGER,                      -- año (negativo = a.C.)
    date_hi       INTEGER,
    attested      BOOLEAN NOT NULL DEFAULT TRUE,
    source_id     TEXT REFERENCES source(id)
);

CREATE TABLE ancestry_edge (
    id            SERIAL PRIMARY KEY,
    child_lect    TEXT NOT NULL REFERENCES lect(id),
    parent_lect   TEXT NOT NULL REFERENCES lect(id),
    kind          edge_kind   NOT NULL,
    law_class     TEXT,                         -- 'Grimm','satem','palatalización' | 'adaptación'
    probability   NUMERIC(4,3) CHECK (probability BETWEEN 0 AND 1),
    status        edge_status NOT NULL,
    crosses_macrosystem BOOLEAN NOT NULL DEFAULT FALSE,   -- almohada=TRUE, pillow=FALSE
    source_id     TEXT REFERENCES source(id),
    CHECK (child_lect <> parent_lect)
);
CREATE INDEX ix_ancestry_child  ON ancestry_edge(child_lect);
CREATE INDEX ix_ancestry_parent ON ancestry_edge(parent_lect);

-- ----------------------------------------------------------------------------
-- Cognate set (= etymon/raíz; red de la FORMA) + protoformas plurales
-- ----------------------------------------------------------------------------
CREATE TABLE cognate_set (
    id            TEXT PRIMARY KEY,             -- 'ie-h2enygh','sem-khadd'
    label         TEXT,                         -- '*h₂enǵʰ- narrow','ḫ-d-d cheek'
    source        TEXT,                         -- 'iecor-gold','wiktionary','de-vaan'
    confidence    NUMERIC(4,3),
    deep_colex    TEXT                          -- colexificación profunda de raíz: 'estrechez↔angustia'
);

CREATE TABLE protoform_hypothesis (             -- PIE plural: varias reconstrucciones en competencia
    id            SERIAL PRIMARY KEY,
    cognate_set_id TEXT NOT NULL REFERENCES cognate_set(id),
    lect_id       TEXT REFERENCES lect(id),     -- el estadio proto (PIE, proto-itálico…)
    form          TEXT NOT NULL,                -- '*h₂enǵʰ-','*h₂emǵʰ-'
    model         TEXT,                         -- 'LIV²','Pokorny','de Vaan'
    probability   NUMERIC(4,3),                 -- por DISTRIBUCIÓN sobre variantes
    status        edge_status NOT NULL DEFAULT 'reconstruido',
    source_id     TEXT REFERENCES source(id)
);

-- ----------------------------------------------------------------------------
-- Formas (entradas) + segmentos + rasgos
-- ----------------------------------------------------------------------------
CREATE TABLE form (
    id            TEXT PRIMARY KEY,             -- 'es·angostura·N·001'
    lect_id       TEXT NOT NULL REFERENCES lect(id),
    concept_id    INTEGER REFERENCES concept(id),
    ipa_raw       TEXT,
    segments_raw  TEXT[],                       -- IPA cruda por segmento
    segments_norm TEXT[],                       -- fonémica normalizada (mata artefacto ʲ)
    orthography   TEXT,
    stress        TEXT,                         -- patrón de acento (hueco por ahora; ver PLAN §4)
    is_loan       BOOLEAN NOT NULL DEFAULT FALSE,
    source_id     TEXT REFERENCES source(id)
);
CREATE INDEX ix_form_lect    ON form(lect_id);
CREATE INDEX ix_form_concept ON form(concept_id);

CREATE TABLE segment (
    id            SERIAL PRIMARY KEY,
    form_id       TEXT NOT NULL REFERENCES form(id) ON DELETE CASCADE,
    pos           INTEGER NOT NULL,
    ipa           TEXT NOT NULL,
    phoneme_norm  TEXT,
    syllable      INTEGER,
    role          TEXT,                         -- onset/nucleus/coda
    is_stressed   BOOLEAN,
    length        TEXT,
    tone          TEXT
);
CREATE INDEX ix_segment_form ON segment(form_id);

CREATE TABLE feature (                          -- panphon + extensiones (rasgo por fonema)
    phoneme       TEXT NOT NULL,
    feat          TEXT NOT NULL,
    value         SMALLINT,
    PRIMARY KEY (phoneme, feat)
);

-- ----------------------------------------------------------------------------
-- Morfología (concatenativa y raíz-y-patrón) + afijos como entradas-morfema
-- ----------------------------------------------------------------------------
CREATE TABLE affix (                            -- sub-, -less: morfema con lineage/sentido/esqueleto propios
    id            TEXT PRIMARY KEY,             -- 'afx·sub','afx·less'
    form          TEXT NOT NULL,
    type          affix_type NOT NULL,
    function_gloss TEXT,                         -- 'bajo/subordinado','sin/carente de'
    grammaticalization TEXT,                    -- '*lausaz suelto → -less sin'
    cons_skeleton TEXT,                         -- esqueleto propio del afijo (letras): 's·b','l·s'
    code          TEXT,                         -- símbolos: 'Σ·Φ','Λ·Σ'
    origin_lect   TEXT REFERENCES lect(id),     -- lengua de origen del afijo (lat, gmc)
    source_id     TEXT REFERENCES source(id)
);

CREATE TABLE morph (
    id            SERIAL PRIMARY KEY,
    form_id       TEXT NOT NULL REFERENCES form(id) ON DELETE CASCADE,
    span_start    INTEGER,
    span_end      INTEGER,
    role          morph_role NOT NULL,
    gloss         TEXT,
    affix_id      TEXT REFERENCES affix(id)     -- si role=affix/pattern
);
CREATE INDEX ix_morph_form  ON morph(form_id);
CREATE INDEX ix_morph_affix ON morph(affix_id);

-- ----------------------------------------------------------------------------
-- Cognacy (red de la FORMA) — con cognación CONDICIONAL a la duda
-- ----------------------------------------------------------------------------
CREATE TABLE cognate_member (
    id            SERIAL PRIMARY KEY,
    cognate_set_id TEXT NOT NULL REFERENCES cognate_set(id),
    form_id       TEXT NOT NULL REFERENCES form(id),
    condition_hyp INTEGER REFERENCES ancestry_edge(id)   -- cognado SÓLO si esta hipótesis del grafo de duda vale (lanza)
);
CREATE INDEX ix_cogmem_set  ON cognate_member(cognate_set_id);
CREATE INDEX ix_cogmem_form ON cognate_member(form_id);

-- ----------------------------------------------------------------------------
-- Redes del SENTIDO: polisemia (intra-lengua) + colexificación
-- (la red de CONCEPTO entre lenguas = via sense.concept_id / form.concept_id compartido)
-- ----------------------------------------------------------------------------
CREATE TABLE sense (
    id            SERIAL PRIMARY KEY,
    form_id       TEXT NOT NULL REFERENCES form(id) ON DELETE CASCADE,
    concept_id    INTEGER REFERENCES concept(id),
    gloss         TEXT,
    context       TEXT
);
CREATE INDEX ix_sense_form    ON sense(form_id);
CREATE INDEX ix_sense_concept ON sense(concept_id);

CREATE TABLE polyseme_link (                    -- sinónimos/acepciones intra-lengua; NO requiere cognación
    id            SERIAL PRIMARY KEY,
    sense_a       INTEGER NOT NULL REFERENCES sense(id) ON DELETE CASCADE,
    sense_b       INTEGER NOT NULL REFERENCES sense(id) ON DELETE CASCADE,
    lect_id       TEXT REFERENCES lect(id),
    relation      TEXT                          -- 'sinónimo','antónimo','acepción'
);

CREATE TABLE colex (                            -- colexificación intra-lengua
    id            SERIAL PRIMARY KEY,
    concept_a     INTEGER NOT NULL REFERENCES concept(id),
    concept_b     INTEGER NOT NULL REFERENCES concept(id),
    lect_id       TEXT REFERENCES lect(id)
);

-- ----------------------------------------------------------------------------
-- Contacto: cohorte de préstamo + sustrato dudoso
-- ----------------------------------------------------------------------------
CREATE TABLE contact_cohort (
    id            TEXT PRIMARY KEY,             -- 'arabismos-al'
    pattern       TEXT,                         -- 'al- fosilizado'
    note          TEXT
);
CREATE TABLE cohort_member (
    id            SERIAL PRIMARY KEY,
    cohort_id     TEXT NOT NULL REFERENCES contact_cohort(id),
    form_id       TEXT NOT NULL REFERENCES form(id)
);

CREATE TABLE substrate_edge (                   -- multi-hipótesis con probabilidad + status=dudoso (lanza)
    id            SERIAL PRIMARY KEY,
    form_id       TEXT NOT NULL REFERENCES form(id),
    source_lect   TEXT REFERENCES lect(id),     -- celtíbero, ibérico…
    probability   NUMERIC(4,3),
    status        edge_status NOT NULL DEFAULT 'dudoso',
    source_id     TEXT REFERENCES source(id)
);

-- ----------------------------------------------------------------------------
-- Capa ENDOLINGÜÍSTICA/CRIPTOLÓGICA: esqueleto (por-estadio) + linaje + operadores + firma
-- ----------------------------------------------------------------------------
CREATE TABLE skeleton_lineage (                 -- agrupa un mismo código a través de estadios y RAMAS (resonancia)
    id            SERIAL PRIMARY KEY,
    code          TEXT NOT NULL                 -- 'Ξ·Χ·Σ·Θ'
);

CREATE TABLE skeleton (
    id            TEXT PRIMARY KEY,             -- 'SK·es·angost·001'
    form_id       TEXT NOT NULL REFERENCES form(id) ON DELETE CASCADE,
    stage_lect_id TEXT REFERENCES lect(id),     -- POR-ESTADIO (Angst: /g/ en AAA, ∅ en moderno)
    cons_skeleton TEXT,                          -- palabra, LETRAS: 'n·g·s·t·ɾ'
    core_skeleton TEXT,                          -- núcleo/raíz, LETRAS: 'n·g·s·t'   (convención: núcleo en letras)
    code          TEXT,                          -- palabra, SÍMBOLOS: 'Ξ·Χ·Σ·Θ·Λ'  (convención: código en símbolos)
    vowels        TEXT,                          -- VOCALES conservadas (secuencia cruda; preserva tono/longitud)
    cv_template   TEXT,                          -- patrón C/V/G (forma completa)
    skeleton_lineage_id INTEGER REFERENCES skeleton_lineage(id)
);
CREATE INDEX ix_skeleton_form    ON skeleton(form_id);
CREATE INDEX ix_skeleton_lineage ON skeleton(skeleton_lineage_id);

CREATE TABLE correspondence (                   -- operador entre estadios/lenguas (derivado); conservar/mutar/truncar
    id            SERIAL PRIMARY KEY,
    from_lect     TEXT REFERENCES lect(id),
    to_lect       TEXT REFERENCES lect(id),
    a             TEXT,                          -- segmento origen
    b             TEXT,                          -- segmento destino
    env           TEXT,                          -- entorno (disparador)
    count         INTEGER,
    corr_type     corr_type,                     -- conservar/mutar/truncar
    law_class     TEXT,                          -- Grimm/satem/palatalización/lenición/adaptación
    crosses_macrosystem BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE crypto (                           -- firma matemática monádica, montada sobre el esqueleto
    form_id       TEXT PRIMARY KEY REFERENCES form(id) ON DELETE CASCADE,
    skeleton_id   TEXT REFERENCES skeleton(id),
    feature_vectors JSONB,                       -- F₂ⁿ por segmento del esqueleto
    self_info     NUMERIC                        -- sorpresa del esqueleto dado el inventario (opcional Fase 0)
);

-- ----------------------------------------------------------------------------
-- Vistas: "toda la historia de la palabra" (linaje) + "resonancia" (mismo esqueleto)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_lineage AS              -- CTE recursiva: sube el grafo desde cada lect
WITH RECURSIVE up AS (
    SELECT e.child_lect AS start_lect, e.child_lect, e.parent_lect, e.kind, e.law_class,
           e.probability, e.status, 1 AS depth
    FROM ancestry_edge e
    UNION ALL
    SELECT u.start_lect, e.child_lect, e.parent_lect, e.kind, e.law_class,
           e.probability, e.status, u.depth + 1
    FROM ancestry_edge e JOIN up u ON e.child_lect = u.parent_lect
)
SELECT * FROM up;

CREATE OR REPLACE VIEW v_resonance AS            -- mismo código de esqueleto entre lects/ramas
SELECT sl.code, array_agg(DISTINCT f.lect_id) AS lects, count(DISTINCT s.form_id) AS n_forms
FROM skeleton s
JOIN skeleton_lineage sl ON s.skeleton_lineage_id = sl.id
JOIN form f ON s.form_id = f.id
GROUP BY sl.code;

COMMIT;
