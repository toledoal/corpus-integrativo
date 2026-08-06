-- ============================================================================
-- Migración v0.3 → v0.4 · alinea la DB viva con schema.sql consolidado
--   - columnas `family` (scope de análisis) en tablas analíticas
--   - índices faltantes (borrados-por-familia y joins) — críticos al escalar
--   - FKs a ON DELETE CASCADE (simplifican borrados incrementales)
-- Idempotente (IF NOT EXISTS / catálogo). Cargar: psql … -f db/migrate_0.4.sql
-- ============================================================================
BEGIN;

-- columnas que existían solo por ALTER en runtime (por si faltan en alguna DB)
ALTER TABLE form         ADD COLUMN IF NOT EXISTS etymology_text TEXT;
ALTER TABLE form         ADD COLUMN IF NOT EXISTS pos TEXT;
ALTER TABLE form         ADD COLUMN IF NOT EXISTS superseded_by TEXT;
ALTER TABLE form         ADD COLUMN IF NOT EXISTS is_proper BOOLEAN;
ALTER TABLE skeleton     ADD COLUMN IF NOT EXISTS is_compound BOOLEAN DEFAULT FALSE;
ALTER TABLE skeleton     ADD COLUMN IF NOT EXISTS core_valid BOOLEAN;
ALTER TABLE cognate_set  ADD COLUMN IF NOT EXISTS ancestor_lect TEXT;
-- nuevas: scope por familia
ALTER TABLE cognate_set    ADD COLUMN IF NOT EXISTS family TEXT;
ALTER TABLE correspondence ADD COLUMN IF NOT EXISTS family TEXT;

-- constraint única requerida por ON CONFLICT(code)
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_sklin_code') THEN
    ALTER TABLE skeleton_lineage ADD CONSTRAINT uq_sklin_code UNIQUE (code);
  END IF;
END $$;

-- índices faltantes
CREATE INDEX IF NOT EXISTS ix_form_source     ON form(source_id);
CREATE INDEX IF NOT EXISTS ix_form_lect_ortho ON form(lect_id, lower(orthography));
CREATE INDEX IF NOT EXISTS ix_formety_parent  ON form_etymology(parent_lect);
CREATE INDEX IF NOT EXISTS ix_formety_kind    ON form_etymology(kind);
CREATE INDEX IF NOT EXISTS ix_skeleton_stage  ON skeleton(stage_lect_id);
CREATE INDEX IF NOT EXISTS ix_cogset_family   ON cognate_set(family);
CREATE INDEX IF NOT EXISTS ix_corr_from       ON correspondence(from_lect);
CREATE INDEX IF NOT EXISTS ix_corr_to         ON correspondence(to_lect);
CREATE INDEX IF NOT EXISTS ix_corr_family     ON correspondence(family);
CREATE INDEX IF NOT EXISTS ix_proto_set       ON protoform_hypothesis(cognate_set_id);
CREATE INDEX IF NOT EXISTS ix_poly_lect       ON polyseme_link(lect_id);
CREATE INDEX IF NOT EXISTS ix_colex_lect      ON colex(lect_id);
CREATE INDEX IF NOT EXISTS ix_cohmem_form     ON cohort_member(form_id);
CREATE INDEX IF NOT EXISTS ix_cohmem_coh      ON cohort_member(cohort_id);
CREATE INDEX IF NOT EXISTS ix_subst_form      ON substrate_edge(form_id);

-- TODA columna-FK indexada: sin índice, borrar el PADRE hace seq-scan del hijo por fila (borrado O(n·m),
-- patológico a escala — fue el bug que colgó la carga germánica 90 min en crypto.skeleton_id/polyseme.sense_*).
CREATE INDEX IF NOT EXISTS ix_poly_sense_a    ON polyseme_link(sense_a);
CREATE INDEX IF NOT EXISTS ix_poly_sense_b    ON polyseme_link(sense_b);
CREATE INDEX IF NOT EXISTS ix_crypto_skel     ON crypto(skeleton_id);
CREATE INDEX IF NOT EXISTS ix_cogmem_cond     ON cognate_member(condition_hyp);
CREATE INDEX IF NOT EXISTS ix_colex_ca        ON colex(concept_a);
CREATE INDEX IF NOT EXISTS ix_colex_cb        ON colex(concept_b);
CREATE INDEX IF NOT EXISTS ix_proto_lect      ON protoform_hypothesis(lect_id);
CREATE INDEX IF NOT EXISTS ix_subst_srclect   ON substrate_edge(source_lect);
CREATE INDEX IF NOT EXISTS ix_affix_origin    ON affix(origin_lect);
CREATE INDEX IF NOT EXISTS ix_affix_source    ON affix(source_id);
CREATE INDEX IF NOT EXISTS ix_ancestry_source ON ancestry_edge(source_id);
CREATE INDEX IF NOT EXISTS ix_formety_source  ON form_etymology(source_id);
CREATE INDEX IF NOT EXISTS ix_lect_source     ON lect(source_id);
CREATE INDEX IF NOT EXISTS ix_proto_source    ON protoform_hypothesis(source_id);

-- FKs a CASCADE (form_etymology sigue a la forma; protoforma sigue al cognate_set)
ALTER TABLE form_etymology DROP CONSTRAINT IF EXISTS form_etymology_child_form_id_fkey;
ALTER TABLE form_etymology ADD  CONSTRAINT form_etymology_child_form_id_fkey
      FOREIGN KEY (child_form_id) REFERENCES form(id) ON DELETE CASCADE;
ALTER TABLE protoform_hypothesis DROP CONSTRAINT IF EXISTS protoform_hypothesis_cognate_set_id_fkey;
ALTER TABLE protoform_hypothesis ADD  CONSTRAINT protoform_hypothesis_cognate_set_id_fkey
      FOREIGN KEY (cognate_set_id) REFERENCES cognate_set(id) ON DELETE CASCADE;
ALTER TABLE cognate_member DROP CONSTRAINT IF EXISTS cognate_member_cognate_set_id_fkey;
ALTER TABLE cognate_member ADD  CONSTRAINT cognate_member_cognate_set_id_fkey
      FOREIGN KEY (cognate_set_id) REFERENCES cognate_set(id) ON DELETE CASCADE;

COMMIT;

ALTER TABLE form ADD COLUMN IF NOT EXISTS ipa_elab TEXT;  -- IPA elaborada por G2P (epitran)
