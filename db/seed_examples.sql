-- Seed de validación (Fase 0): angostura (es) + Angst (de) + angustus (la), cognados por *h₂enǵʰ-.
-- Demuestra: grafo de linaje, PIE plural, cognate_set entre ramas, esqueleto por-estadio + resonancia.
BEGIN;

-- Fuentes (con licencia + redistribuible)
INSERT INTO source(id,citation,url,kind,license,redistributable) VALUES
 ('wiktionary','Wiktionary (via Kaikki/wiktextract)','https://kaikki.org','diccionario','CC-BY-SA-3.0',TRUE),
 ('iecor','Heggarty et al. 2023, IE-CoR','https://iecor.clld.org','cognación oro','CC-BY-4.0',TRUE),
 ('liv','LIV² (LiLa linked data)','','reconstrucción','CC-BY-SA-4.0',TRUE),
 ('devaan','de Vaan, EDL','','reconstrucción','copyright',FALSE),
 ('kroonen','Kroonen, EDPG','','reconstrucción','copyright',FALSE);

-- Conceptos
INSERT INTO concept(concepticon_id,gloss_en,gloss_de) VALUES
 ('1','narrowness','Enge'),('2','fear','Angst');

-- Lects (escalera) — 2 ramas + PIE compartido
INSERT INTO lect(id,name,level,macrosystem,date_lo,date_hi,attested,source_id) VALUES
 ('pie','Proto-Indo-European','pie','indo-europeo',-4500,-2500,FALSE,'liv'),
 ('proto-italic','Proto-Italic','proto_rama','indo-europeo',-1500,-700,FALSE,'devaan'),
 ('la','Latin','lengua','indo-europeo',-200,200,TRUE,'iecor'),
 ('es','Spanish','lengua','indo-europeo',1200,2026,TRUE,'wiktionary'),
 ('pgmc','Proto-Germanic','proto_rama','indo-europeo',-500,200,FALSE,'kroonen'),
 ('goh','Old High German','lengua','indo-europeo',750,1050,TRUE,'wiktionary'),
 ('de','German','lengua','indo-europeo',1500,2026,TRUE,'wiktionary');

-- Grafo de linaje (herencia)
INSERT INTO ancestry_edge(child_lect,parent_lect,kind,law_class,probability,status,source_id) VALUES
 ('es','la','herencia','lenición/palatalización',0.98,'atestiguado','wiktionary'),
 ('la','proto-italic','herencia',NULL,0.9,'reconstruido','devaan'),
 ('proto-italic','pie','herencia',NULL,0.85,'reconstruido','liv'),
 ('de','goh','herencia',NULL,0.98,'atestiguado','wiktionary'),
 ('goh','pgmc','herencia','Grimm',0.95,'reconstruido','kroonen'),
 ('pgmc','pie','herencia','Grimm',0.9,'reconstruido','liv');

-- Cognate set (etymon raíz) + PIE PLURAL (varias reconstrucciones, prob por distribución)
INSERT INTO cognate_set(id,label,source,confidence,deep_colex) VALUES
 ('ie-h2engh','*h₂enǵʰ- ''narrow, tight''','iecor+liv',0.9,'estrechez↔angustia');
INSERT INTO protoform_hypothesis(cognate_set_id,lect_id,form,model,probability,source_id) VALUES
 ('ie-h2engh','pie','*h₂enǵʰ-','LIV²',0.55,'liv'),
 ('ie-h2engh','pie','*h₂emǵʰ-','Pokorny',0.25,'devaan'),
 ('ie-h2engh','pie','*h₂énǵʰ-os-','de Vaan',0.20,'devaan');

-- Formas
INSERT INTO form(id,lect_id,concept_id,ipa_raw,segments_norm,orthography,stress,source_id) VALUES
 ('la·angustus·A·001','la',(SELECT id FROM concept WHERE gloss_en='narrowness'),
   'aŋgustus',ARRAY['a','n','g','u','s','t','u','s'],'angustus',NULL,'iecor'),
 ('es·angostura·N·001','es',(SELECT id FROM concept WHERE gloss_en='narrowness'),
   'aŋgosˈtuɾa',ARRAY['a','n','g','o','s','t','u','ɾ','a'],'angostura','penúltima','wiktionary'),
 ('de·Angst·N·001','de',(SELECT id FROM concept WHERE gloss_en='fear'),
   'aŋst',ARRAY['a','n','s','t'],'Angst','inicial','wiktionary');

-- Sentidos (angostura polisémica; Angst) — red del SENTIDO
INSERT INTO sense(form_id,concept_id,gloss,context) VALUES
 ('es·angostura·N·001',(SELECT id FROM concept WHERE gloss_en='narrowness'),'estrechez','cualidad de angosto'),
 ('es·angostura·N·001',NULL,'paso/estrecho','estrecho de un río o montaña'),
 ('de·Angst·N·001',(SELECT id FROM concept WHERE gloss_en='fear'),'miedo, angustia','die Angst');

-- Cognacy (red de la FORMA): las tres formas en el mismo etymon
INSERT INTO cognate_member(cognate_set_id,form_id) VALUES
 ('ie-h2engh','la·angustus·A·001'),('ie-h2engh','es·angostura·N·001'),('ie-h2engh','de·Angst·N·001');

-- Esqueleto: linaje compartido Ξ·Χ·Σ·Θ (resonancia entre ramas), por-estadio
INSERT INTO skeleton_lineage(code) VALUES ('Ξ·Χ·Σ·Θ');
INSERT INTO skeleton(id,form_id,stage_lect_id,cons_skeleton,core_skeleton,code,skeleton_lineage_id) VALUES
 ('SK·la·angust·001','la·angustus·A·001','la','n·g·s·t','n·g·s·t','Ξ·Χ·Σ·Θ',
   (SELECT id FROM skeleton_lineage WHERE code='Ξ·Χ·Σ·Θ')),
 ('SK·es·angost·001','es·angostura·N·001','es','n·g·s·t·ɾ','n·g·s·t','Ξ·Χ·Σ·Θ·Λ',
   (SELECT id FROM skeleton_lineage WHERE code='Ξ·Χ·Σ·Θ')),
 -- Angst en estadio AAA (goh): el /g/ aún presente → mismo código de raíz (resonancia germánica↔itálica)
 ('SK·goh·angust·001','de·Angst·N·001','goh','n·g·s·t','n·g·s·t','Ξ·Χ·Σ·Θ',
   (SELECT id FROM skeleton_lineage WHERE code='Ξ·Χ·Σ·Θ'));

-- Correspondencia (operador dirigido, ejemplo): latín→español, conserva esqueleto (solo cambia vocal/desin.)
INSERT INTO correspondence(from_lect,to_lect,a,b,env,corr_type,law_class) VALUES
 ('la','es','u','o','_[C]','conservar','—'),          -- consonantes conservadas; cambio vocálico ŭ→o
 ('la','es','k','θ','_V[frontal]','mutar','palatalización');  -- (cf. lancea→lanza, otra entrada)

COMMIT;
