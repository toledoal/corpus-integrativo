#!/usr/bin/env python3
"""Visor del corpus — DATA-FIRST: por entrada, TODA la historia de la palabra (PLAN §3f).

Lidera con la palabra, su lengua (rama/familia), sus SENTIDOS, su ETIMOLOGÍA (prosa + linaje estructurado) y sus
COGNADOS. La fonética (IPA, segmentos) va después; el análisis endolingüístico (esqueleto/código OAS) va DISCRETO
al final — es una capa derivada, no el titular (PLAN §6e: OAS aplazado).

Uso:  .venv/bin/python viewer/serve.py     →  http://localhost:8080
"""
import json
import sys
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingest"))
import psycopg
from config import DSN
from families import FAMILIES

PORT = int(os.environ.get("CI_VIEWER_PORT", "8080"))
BRANCH = {}
for _f, _c in FAMILIES.items():
    for _m in _c["members"]:
        BRANCH.setdefault(_m, _f)


def db():
    return psycopg.connect(DSN)


def lects():
    with db() as c, c.cursor() as cur:
        cur.execute("""SELECT l.id, l.name, l.subgroup, count(f.id) FROM lect l JOIN form f ON f.lect_id=l.id
                       WHERE f.source_id='kaikki' GROUP BY 1,2,3 HAVING count(f.id)>0 ORDER BY 4 DESC""")
        out = []
        for lid, name, sub, n in cur.fetchall():
            out.append({"id": lid, "name": name or lid, "branch": BRANCH.get(lid, "—"), "subgroup": sub, "n": n})
        return out


def search(q, lect):
    with db() as c, c.cursor() as cur:
        base = "SELECT id, lect_id, orthography FROM form WHERE source_id='kaikki'"
        if lect:
            cur.execute(base + " AND lower(orthography)=lower(%s) AND lect_id=%s LIMIT 80", (q, lect))
        else:
            cur.execute(base + " AND lower(orthography)=lower(%s) LIMIT 80", (q,))
        rows = cur.fetchall()
        if not rows:
            args = (q + "%", lect) if lect else (q + "%",)
            cur.execute(base + " AND lower(orthography) LIKE lower(%s)" + (" AND lect_id=%s" if lect else "") + " LIMIT 80", args)
            rows = cur.fetchall()
        return [{"id": r[0], "lect": r[1], "word": r[2]} for r in rows]


def concepts(q):
    """Busca CONCEPTOS Concepticon por glosa inglesa → lista con nº de formas (todas las fuentes)."""
    with db() as c, c.cursor() as cur:
        cur.execute("""SELECT c.id, COALESCE(c.gloss_en,c.concepticon_gloss), c.semantic_field, c.concepticon_id,
                              (SELECT count(*) FROM form f WHERE f.concept_id=c.id)
                       FROM concept c
                       WHERE c.gloss_en ILIKE %s OR c.concepticon_gloss ILIKE %s
                       ORDER BY 5 DESC LIMIT 80""", (q + "%", q + "%"))
        out = [{"id": r[0], "gloss": r[1], "field": r[2], "ccid": r[3], "n": r[4]} for r in cur.fetchall()]
        if not out:                                  # fallback: coincidencia en cualquier parte
            cur.execute("""SELECT c.id, COALESCE(c.gloss_en,c.concepticon_gloss), c.semantic_field, c.concepticon_id,
                                  (SELECT count(*) FROM form f WHERE f.concept_id=c.id)
                           FROM concept c WHERE c.gloss_en ILIKE %s OR c.concepticon_gloss ILIKE %s
                           ORDER BY 5 DESC LIMIT 80""", ("%" + q + "%", "%" + q + "%"))
            out = [{"id": r[0], "gloss": r[1], "field": r[2], "ccid": r[3], "n": r[4]} for r in cur.fetchall()]
        return out


def concept_forms(cid, family):
    """Todas las formas de un concepto a través de lenguas, ordenadas por familia→lengua (para navegar por sentido)."""
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT COALESCE(gloss_en,concepticon_gloss), semantic_field, concepticon_id FROM concept WHERE id=%s", (cid,))
        cr = cur.fetchone()
        q = """SELECT f.id, f.lect_id, l.name, l.family, l.subgroup, f.orthography, f.source_id
               FROM form f JOIN lect l ON l.id=f.lect_id WHERE f.concept_id=%s"""
        args = [cid]
        if family:
            q += " AND l.family=%s"; args.append(family)
        q += " ORDER BY l.family NULLS LAST, l.name, lower(normalize(f.orthography,NFC)) LIMIT 4000"
        cur.execute(q, args)
        seen, rows = {}, []                          # dedup por (lengua, forma normalizada); agrega fuentes
        for r in cur.fetchall():
            k = (r[1], (r[5] or "").lower())
            if k in seen:
                if r[6] not in seen[k]["source"]:
                    seen[k]["source"] += "," + r[6]
                continue
            o = {"id": r[0], "lect": r[1], "lect_name": r[2] or r[1], "family": r[3] or "—",
                 "branch": BRANCH.get(r[1], r[3] or "—"), "word": r[5], "source": r[6]}
            seen[k] = o; rows.append(o)
            if len(rows) >= 600:
                break
        # familias disponibles para el filtro
        cur.execute("SELECT DISTINCT l.family FROM form f JOIN lect l ON l.id=f.lect_id WHERE f.concept_id=%s AND l.family IS NOT NULL ORDER BY 1", (cid,))
        fams = [r[0] for r in cur.fetchall()]
        return {"gloss": cr[0] if cr else "?", "field": cr[1] if cr else None, "ccid": cr[2] if cr else None,
                "forms": rows, "families": fams, "truncated": len(rows) >= 600}


def detail(fid):
    with db() as c, c.cursor() as cur:
        cur.execute("""SELECT f.lect_id, f.orthography, f.ipa_raw, f.ipa_elab, f.pos, f.etymology_text,
                       f.is_proper, f.source_id, f.is_loan, l.name, l.subgroup, l.level
                       FROM form f LEFT JOIN lect l ON l.id=f.lect_id WHERE f.id=%s""", (fid,))
        r = cur.fetchone()
        if not r:
            return {"error": "no encontrado"}
        d = {"id": fid, "lect": r[0], "word": r[1], "ipa_raw": r[2], "ipa_elab": r[3], "pos": r[4],
             "etymology_text": r[5], "is_proper": r[6], "source": r[7], "is_loan": r[8],
             "lect_name": r[9], "subgroup": r[10], "level": r[11], "branch": BRANCH.get(r[0], "—")}
        cur.execute("SELECT gloss FROM sense WHERE form_id=%s AND gloss IS NOT NULL LIMIT 30", (fid,))
        d["senses"] = [g[0] for g in cur.fetchall()]
        cur.execute("SELECT count(*) FROM polyseme_link pl JOIN sense s ON s.id=pl.sense_a WHERE s.form_id=%s", (fid,))
        d["polyseme_links"] = cur.fetchone()[0]
        # LINAJE COMPLETO "toda la historia" (§3f): walk recursivo hacia arriba, encadenando por parent_form_id,
        # hasta PIE y más allá. Cycle-safe (path array + tope de profundidad).
        cur.execute("""WITH RECURSIVE up AS (
                         SELECT fe.parent_lect, fe.parent_form, fe.parent_form_id, fe.kind, fe.source_id,
                                1 AS depth, ARRAY[fe.child_form_id] AS path
                         FROM form_etymology fe WHERE fe.child_form_id=%s
                         UNION ALL
                         SELECT fe.parent_lect, fe.parent_form, fe.parent_form_id, fe.kind, fe.source_id,
                                up.depth+1, up.path||fe.child_form_id
                         FROM form_etymology fe JOIN up ON fe.child_form_id=up.parent_form_id
                         WHERE up.depth<15 AND NOT fe.child_form_id = ANY(up.path)
                           AND up.kind IN ('herencia','reconstruido'))   -- NO trepar por préstamo/sustrato: la
                       --   historia profunda de un préstamo es del DONANTE, no de quien lo toma (caso 'gato'→gâteau)
                       SELECT DISTINCT ON (up.parent_lect, up.parent_form)
                              up.parent_lect, up.parent_form, up.kind, up.source_id, up.depth, l.name, l.level
                       FROM up LEFT JOIN lect l ON l.id=up.parent_lect
                       ORDER BY up.parent_lect, up.parent_form, up.depth""", (fid,))
        _RANK = {"idiolecto": 0, "dialecto": 1, "lengua": 2, "estadio": 3, "subfamilia": 4,
                 "proto_rama": 5, "pie": 6, "nostratico": 7}
        lin = [{"lect": r[0], "form": r[1], "kind": r[2], "src": r[3], "depth": r[4],
                "lect_name": r[5], "rank": _RANK.get(r[6], 2)} for r in cur.fetchall()]
        lin.sort(key=lambda x: (x["rank"], x["depth"]))     # más cercano primero → PIE al final
        for i, x in enumerate(lin):
            x["depth"] = i + 1                               # profundidad de despliegue por posición en la cadena
        d["etymology"] = lin
        d["reaches_pie"] = any(x["lect"] == "ine-pro" for x in lin)
        d["deepest"] = (lin[-1]["lect_name"] or lin[-1]["lect"]) if lin else None
        # COGNADOS unificados: unión de TODOS los cognate_sets del form, deduplicados por (lengua, forma
        # normalizada NFC) para no repetir (una palabra que está en varios sets solapados se muestra UNA vez),
        # con las fuentes que la atestiguan agregadas. Evita las tarjetas redundantes.
        cur.execute("""WITH sets AS (SELECT DISTINCT cognate_set_id FROM cognate_member WHERE form_id=%s)
                       SELECT f.lect_id, max(l.name) AS lname,
                              (array_agg(f.orthography ORDER BY length(f.orthography), f.id))[1] AS word,
                              min(g.gloss) AS gloss,
                              string_agg(DISTINCT cs.source, ', ' ORDER BY cs.source) AS srcs
                       FROM sets
                       JOIN cognate_member cm ON cm.cognate_set_id=sets.cognate_set_id
                       JOIN cognate_set cs ON cs.id=sets.cognate_set_id
                       JOIN form f ON f.id=cm.form_id
                       LEFT JOIN lect l ON l.id=f.lect_id
                       LEFT JOIN LATERAL (SELECT gloss FROM sense s WHERE s.form_id=f.id AND gloss IS NOT NULL LIMIT 1) g ON true
                       GROUP BY f.lect_id, lower(normalize(f.orthography, NFC))
                       ORDER BY f.lect_id, word
                       LIMIT 150""", (fid,))
        rows = cur.fetchall()
        cur.execute("SELECT count(DISTINCT cognate_set_id), string_agg(DISTINCT cs.source, ', ') "
                    "FROM cognate_member cm JOIN cognate_set cs ON cs.id=cm.cognate_set_id WHERE cm.form_id=%s", (fid,))
        nsets, allsrc = cur.fetchone()
        d["cognates"] = [{"lect": r[0], "lect_name": r[1], "word": r[2], "gloss": r[3], "srcs": r[4]} for r in rows]
        d["cognate_meta"] = {"n_sets": nsets or 0, "sources": allsrc or ""}
        # RED DE SIGNIFICADO — conceptos de la forma (de sus SENTIDOS + form.concept_id) + colexificación global
        cur.execute("""SELECT DISTINCT c.id, COALESCE(c.gloss_en,c.concepticon_gloss)
                       FROM concept c WHERE c.id IN (
                         SELECT concept_id FROM sense WHERE form_id=%s AND concept_id IS NOT NULL
                         UNION SELECT concept_id FROM form WHERE id=%s AND concept_id IS NOT NULL)
                       ORDER BY 2""", (fid, fid))
        cc = cur.fetchall()
        d["concepts"] = [r[1] for r in cc]
        d["colex"] = []
        cids = [r[0] for r in cc]
        if cids:
            cur.execute("""SELECT COALESCE(c.gloss_en,c.concepticon_gloss) g,
                                  count(DISTINCT x.lect_id) langs, count(DISTINCT l.family) fams
                           FROM colex x
                           JOIN concept c ON c.id = CASE WHEN x.concept_a = ANY(%s) THEN x.concept_b ELSE x.concept_a END
                           LEFT JOIN lect l ON l.id=x.lect_id
                           WHERE (x.concept_a = ANY(%s) OR x.concept_b = ANY(%s))
                             AND NOT (x.concept_a = ANY(%s) AND x.concept_b = ANY(%s))
                           GROUP BY 1 ORDER BY 2 DESC LIMIT 15""", (cids, cids, cids, cids, cids))
            d["colex"] = [{"concept": r[0], "langs": r[1], "families": r[2]} for r in cur.fetchall()]
        # morfología: un código POR MORFEMA, con la RAÍZ marcada (decomposición por etimología)
        cur.execute("""SELECT role, surface, gloss, cons_skeleton, code FROM morph
                       WHERE form_id=%s ORDER BY morph_ord NULLS LAST, id""", (fid,))
        d["morphemes"] = [{"role": m[0], "surface": m[1] or m[2], "cons": m[3], "code": m[4]} for m in cur.fetchall()]
        # análisis (secundario)
        cur.execute("SELECT cons_skeleton, code, core_skeleton, vowels, cv_template, is_compound FROM skeleton WHERE form_id=%s", (fid,))
        s = cur.fetchone()
        d["skeleton"] = ({"cons": s[0], "code": s[1], "core": s[2], "vowels": s[3], "cv": s[4], "compound": s[5]} if s else None)
        # código de la RAÍZ = el de la morph raíz (si la decomposición existe)
        root = next((m for m in d["morphemes"] if m["role"] == "root" and m["code"]), None)
        d["root_code"] = root["code"] if root else None
        d["root_surface"] = root["surface"] if root else None
        cur.execute("SELECT ipa, is_stressed FROM segment WHERE form_id=%s ORDER BY pos", (fid,))
        d["segments"] = [{"ipa": g[0], "stress": g[1]} for g in cur.fetchall()]
        cur.execute("SELECT self_info FROM crypto WHERE form_id=%s", (fid,))
        cy = cur.fetchone()
        d["self_info"] = float(cy[0]) if cy and cy[0] is not None else None
        return d


PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Corpus Integrativo · visor</title>
<style>
 :root{--bg:#fbfaf7;--fg:#1c1a17;--mut:#726c62;--acc:#3a6ea5;--card:#fff;--line:#e7e3da;--soft:#f1ede4;--warn:#a8641c}
 @media(prefers-color-scheme:dark){:root{--bg:#15140f;--fg:#e9e5db;--mut:#9a948a;--acc:#7db0e0;--card:#1e1c16;--line:#312c22;--soft:#24211a;--warn:#d09a54}}
 *{box-sizing:border-box}body{margin:0;font:15px/1.55 ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--fg)}
 header{padding:12px 20px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:2;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
 h1{font-size:15px;margin:0;font-weight:600;letter-spacing:.02em;color:var(--mut)}h1 b{color:var(--fg)}
 input,select{padding:8px 11px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font-size:15px}
 input#q{min-width:260px}button{padding:8px 16px;border:0;border-radius:8px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer}
 main{display:grid;grid-template-columns:240px 1fr;min-height:calc(100vh - 58px)}
 #results{border-right:1px solid var(--line);overflow:auto;max-height:calc(100vh - 58px)}
 .r{padding:9px 16px;border-bottom:1px solid var(--line);cursor:pointer}.r:hover{background:var(--soft)}.r.sel{background:var(--soft);border-left:3px solid var(--acc)}
 .r b{font-weight:600}.r .lc{color:var(--mut);font-size:12px;margin-left:6px}
 #detail{padding:22px 30px;overflow:auto;max-height:calc(100vh - 58px);max-width:920px}
 .word{font-size:34px;font-weight:700;line-height:1.1}
 .meta{color:var(--mut);margin:6px 0 2px;font-size:14px}.meta b{color:var(--fg);font-weight:600}
 .sec{margin:22px 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--acc);font-weight:700;border-bottom:1px solid var(--line);padding-bottom:4px}
 .prose{background:var(--soft);border-left:3px solid var(--acc);padding:10px 14px;border-radius:0 8px 8px 0;margin:6px 0}
 code,.mono{font-family:ui-monospace,monospace;background:var(--soft);padding:1px 6px;border-radius:5px}
 .sens{margin:3px 0}.sens .n{color:var(--mut);margin-right:8px}
 .tag{display:inline-block;padding:1px 8px;border-radius:20px;background:var(--soft);font-size:12px;margin-right:6px;color:var(--mut)}
 .lin{padding:4px 0}.lin .kind{color:var(--warn);font-size:12px;text-transform:uppercase;margin-right:8px}
 .cog{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0;background:var(--card)}
 .cog h4{margin:0 0 6px;font-size:13px;font-weight:600}.cog .src{color:var(--mut);font-weight:400;font-size:12px}
 table{border-collapse:collapse;width:100%}td{padding:3px 8px;border-bottom:1px solid var(--line);font-size:14px;vertical-align:top}
 td.lc{color:var(--fg);white-space:nowrap;width:1%}td.gl{color:var(--mut)}
 .iso{color:var(--mut);font-size:11px;font-family:ui-monospace,monospace}
 td.srccol{text-align:right;white-space:nowrap}.src2{display:inline-block;font-size:10px;color:var(--mut);background:var(--soft);border-radius:4px;padding:0 5px;margin-left:3px}
 .colx{line-height:2}.cxlead{font-weight:700;color:var(--acc);text-transform:uppercase;font-size:13px;letter-spacing:.03em}
 .cxchip{display:inline-block;padding:2px 9px;margin:2px;border:1px solid var(--line);border-radius:20px;background:var(--card);font-size:13px}
 .cxn{color:var(--mut);font-size:11px}
 .cfam{margin:12px 0 2px;font-weight:700;font-size:13px;color:var(--acc)}
 .back{display:inline-block;margin-bottom:10px;padding:5px 12px;border:1px solid var(--line);border-radius:8px;background:var(--soft);cursor:pointer;font-size:13px;font-weight:600;color:var(--acc)}
 .back:hover{background:var(--card)}
 .cfam:first-of-type{margin-top:2px}
 .pie{display:inline-block;font-size:10px;font-weight:700;color:#fff;background:var(--acc);border-radius:4px;padding:0 6px;letter-spacing:.04em}
 .mbreak{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin:2px 0 4px}
 .mchip{display:inline-flex;gap:5px;align-items:center;padding:3px 9px;border:1px solid var(--line);border-radius:7px;background:var(--card);font-size:13px}
 .mchip.root{border-color:var(--acc);background:color-mix(in srgb,var(--acc) 10%,var(--card))}
 .mchip code{background:var(--soft)}.mchip.root code{background:var(--card);color:var(--acc);font-weight:700}
 .rlbl{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--acc);font-weight:700}
 .plus{color:var(--mut);margin:0 2px}.rootcode{margin-bottom:8px}.rootcode .big,.anal code.big{font-size:16px}
 .anal code.big{background:var(--card);color:var(--acc);font-weight:700;padding:2px 9px}.subline{margin-top:8px}
 .seg{display:inline-block;padding:2px 7px;margin:2px;border:1px solid var(--line);border-radius:6px;font-family:ui-monospace,monospace}
 .seg.st{border-color:var(--acc);color:var(--acc);font-weight:700}
 .anal{background:var(--soft);border-radius:8px;padding:12px 14px;margin-top:6px;font-size:13px;color:var(--mut)}
 .anal code{background:var(--card)}.anal .lbl{color:var(--mut);text-transform:uppercase;font-size:11px;letter-spacing:.04em}
 .mut{color:var(--mut)}.hint{color:var(--mut);padding:42px 30px}
</style></head><body>
<header><h1>Corpus <b>Integrativo</b></h1>
 <form onsubmit="return go(event)" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
  <select id="mode" title="modo de búsqueda"><option value="word">palabra</option><option value="concept">concepto (EN)</option></select>
  <input id="q" placeholder="palabra (cualquier alfabeto)…" autofocus>
  <select id="lc"><option value="">— todas las lenguas —</option></select>
  <button>Buscar</button></form>
 <span id="branchinfo" class="mut" style="font-size:13px"></span></header>
<main><div id="results"></div><div id="detail"><div class="hint">Busca una palabra para ver toda su información.</div></div></main>
<script>
let LECTS={};let CBACK=null;   // contexto del concepto actual, para el botón "volver"
async function loadLects(){const ls=await (await fetch('/api/lects')).json();const sel=document.getElementById('lc');
 ls.forEach(l=>{LECTS[l.id]=l;const o=document.createElement('option');o.value=l.id;
  o.textContent=l.name+' — '+l.branch+(l.subgroup?' / '+l.subgroup:'')+' ('+l.n+')';sel.appendChild(o);});}
document.getElementById('lc')?.addEventListener('change',e=>{const l=LECTS[e.target.value];
 document.getElementById('branchinfo').textContent=l?('rama: '+l.branch+(l.subgroup?' · '+l.subgroup:'')+' · '+l.n+' formas'):'';});
function esc(s){return (s==null?'':''+s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
document.getElementById('mode')?.addEventListener('change',e=>{
 const cm=e.target.value==='concept';
 document.getElementById('q').placeholder=cm?'concepto en inglés (water, dog, mother…)':'palabra (cualquier alfabeto)…';
 document.getElementById('lc').style.display=cm?'none':'';});
async function go(e){e&&e.preventDefault();
 if(document.getElementById('mode').value==='concept')return goConcept();
 const q=document.getElementById('q').value.trim();const lc=document.getElementById('lc').value;
 if(!q)return false;const rs=await (await fetch('/api/search?q='+encodeURIComponent(q)+'&lect='+encodeURIComponent(lc))).json();
 const R=document.getElementById('results');R.innerHTML=rs.length?'':'<div class="hint">sin resultados</div>';
 rs.forEach(r=>{const d=document.createElement('div');d.className='r';d.innerHTML='<b>'+esc(r.word)+'</b><span class="lc">'+r.lect+'</span>';
  d.onclick=()=>{[...R.children].forEach(x=>x.classList.remove('sel'));d.classList.add('sel');show(r.id);};R.appendChild(d);});
 if(rs.length)R.firstChild.click();return false;}
async function goConcept(){const q=document.getElementById('q').value.trim();if(!q)return false;
 const cs=await (await fetch('/api/concepts?q='+encodeURIComponent(q))).json();
 const R=document.getElementById('results');R.innerHTML=cs.length?'':'<div class="hint">sin conceptos</div>';
 cs.forEach(c=>{const d=document.createElement('div');d.className='r';
  d.innerHTML='<b>'+esc(c.gloss)+'</b><span class="lc">'+c.n+' formas</span>'+(c.field?'<div class="mut" style="font-size:11px">'+esc(c.field)+'</div>':'');
  d.onclick=()=>{[...R.children].forEach(x=>x.classList.remove('sel'));d.classList.add('sel');showConcept(c.id,'');};R.appendChild(d);});
 if(cs.length)R.firstChild.click();return false;}
async function showConcept(cid,family){const d=await (await fetch('/api/concept?id='+encodeURIComponent(cid)+'&family='+encodeURIComponent(family||''))).json();
 const D=document.getElementById('detail');CBACK={cid:cid,family:family||'',gloss:d.gloss};
 const lname=(lc,nm)=>nm||(LECTS[lc]&&LECTS[lc].name)||lc;
 let famsel='<select onchange="showConcept(\''+cid+'\',this.value)"><option value="">— todas las familias ('+d.forms.length+(d.truncated?'+':'')+') —</option>'+
   (d.families||[]).map(f=>'<option value="'+esc(f)+'"'+(f===family?' selected':'')+'>'+esc(f)+'</option>').join('')+'</select>';
 let rowsByFam={};(d.forms||[]).forEach(r=>{(rowsByFam[r.family]=rowsByFam[r.family]||[]).push(r);});
 let body=Object.keys(rowsByFam).map(fam=>'<div class="cfam">'+esc(fam)+' <span class="mut">('+rowsByFam[fam].length+')</span></div>'+
   '<table>'+rowsByFam[fam].map(r=>'<tr onclick="show(\''+r.id.replace(/'/g,"\\'")+'\',1)" style="cursor:pointer">'+
     '<td class="lc">'+esc(r.lect_name)+' <span class="iso">'+esc(r.lect)+'</span></td><td><b>'+esc(r.word)+'</b></td>'+
     '<td class="srccol"><span class="src2">'+esc(r.source)+'</span></td></tr>').join('')+'</table>').join('');
 D.innerHTML='<div class="word">'+esc(d.gloss)+'</div>'+
   '<div class="meta">concepto Concepticon'+(d.ccid?' #'+esc(d.ccid):'')+(d.field?' · <b>'+esc(d.field)+'</b>':'')+' · '+(d.forms||[]).length+(d.truncated?'+':'')+' formas'+
   (d.truncated?' <span class="mut">(tope 600 — filtra por familia)</span>':'')+'</div>'+
   '<div class="sec">Formas por lengua '+famsel+'</div>'+body;}
async function show(id,back){const d=await (await fetch('/api/form?id='+encodeURIComponent(id))).json();const D=document.getElementById('detail');
 const sk=d.skeleton||{};
 let sens=(d.senses||[]).map((g,i)=>'<div class="sens"><span class="n">'+(i+1)+'.</span>'+esc(g)+'</div>').join('')||'<span class="mut">—</span>';
 const lname=(lc,nm)=>nm||(LECTS[lc]&&LECTS[lc].name)||lc;
 const lcell=(lc,nm)=>esc(lname(lc,nm))+' <span class="iso">'+esc(lc)+'</span>';
 let lin=(d.etymology||[]).map(e=>'<div class="lin" style="margin-left:'+((e.depth-1)*16)+'px">'+
   '<span class="mut">↑</span> <span class="kind">'+esc(e.kind||'')+'</span>'+lcell(e.lect,e.lect_name)+
   ' <i>'+esc(e.form)+'</i>'+(e.lect==='ine-pro'?' <span class="pie">PIE</span>':'')+
   (e.src?' <span class="iso">· '+esc(e.src)+'</span>':'')+'</div>').join('');
 const SRCLBL={'kaikki-cog':'cog','kaikki-etymology':'etim','iecor-gold':'iecor★','liv':'LIV²'};
 const srcb=s=>(s||'').split(', ').map(x=>'<span class="src2">'+esc(SRCLBL[x]||x)+'</span>').join(' ');
 const cg=(d.cognates||[]); const cm=d.cognate_meta||{};
 let cogs=cg.length?('<div class="cog"><h4>'+cg.length+' coderivados <span class="src">· '+
   (cm.n_sets>1?cm.n_sets+' conjuntos · ':'')+esc(cm.sources||'')+'</span></h4>'+
   '<table>'+cg.map(m=>'<tr><td class="lc">'+lcell(m.lect,m.lect_name)+'</td><td>'+esc(m.word)+'</td>'+
     '<td class="gl">'+esc(m.gloss||'')+'</td><td class="srccol">'+srcb(m.srcs)+'</td></tr>').join('')+
   '</table></div>'):'<span class="mut">no ligado a cognados aún</span>';
 const CC=(d.concepts||[]);
 let colex=CC.length?('<div class="colx">'+
   '<div>'+CC.map(g=>'<span class="cxlead">'+esc(g)+'</span>').join(' <span class="mut">+</span> ')+
     (CC.length>1?' <span class="mut">(esta palabra ya colexifica '+CC.length+' conceptos)</span>':'')+'</div>'+
   ((d.colex||[]).length?'<div style="margin-top:4px"><span class="mut">se colexifica cross-lingüísticamente con</span> '+
     d.colex.map(x=>'<span class="cxchip">'+esc(x.concept)+' <span class="cxn">'+x.langs+' leng'+(x.families>1?' · '+x.families+' fam':'')+'</span></span>').join('')+'</div>'
    :'<div class="mut">— sin colexificaciones cross-lingüísticas registradas</div>')+'</div>'):'';
 let morphs=(d.morphemes||[]);
 let endo;
 if(morphs.length){
   let chips=morphs.map(m=>'<span class="mchip'+(m.role==='root'?' root':'')+'">'+esc(m.surface)+' <code>'+esc(m.code||'∅')+'</code>'+(m.role==='root'?' <span class="rlbl">raíz</span>':'')+'</span>').join('<span class="plus">+</span>');
   endo='<div class="anal">'+
     (d.root_code?'<div class="rootcode"><span class="lbl">código de la raíz</span> <span class="mut">('+esc(d.root_surface)+')</span> <code class="big">'+esc(d.root_code)+'</code></div>':'')+
     '<div class="mbreak">'+chips+'</div>'+
     '<div class="subline"><span class="lbl">núcleo</span> <code>'+esc(sk.core||'—')+'</code> · <span class="lbl">forma completa</span> <code>'+esc(sk.code||'—')+'</code>'+(sk.compound?' <span class="tag">univerbación</span>':'')+
      ' · <span class="lbl">vocales</span> <code>'+esc(sk.vowels||'—')+'</code>'+(d.self_info!=null?' · <span class="lbl">self-info</span> <code>'+d.self_info.toFixed(2)+'</code>':'')+'</div></div>';
 } else {
   endo='<div class="anal"><span class="lbl">código (forma superficial)</span> <code class="big">'+esc(sk.code||'—')+'</code> <span class="mut">— raíz sin segmentar aún</span>'+
     ' · <span class="lbl">esqueleto</span> <code>'+esc(sk.cons||'—')+'</code> · <span class="lbl">vocales</span> <code>'+esc(sk.vowels||'—')+'</code>'+
     (d.self_info!=null?' · <span class="lbl">self-info</span> <code>'+d.self_info.toFixed(2)+'</code>':'')+'</div>';
 }
 let segs=(d.segments||[]).map(s=>'<span class="seg'+(s.stress?' st':'')+'">'+esc(s.ipa)+'</span>').join('')||'<span class="mut">—</span>';
 D.innerHTML=(back&&CBACK?'<div class="back" onclick="showConcept(CBACK.cid,CBACK.family)">← volver a «'+esc(CBACK.gloss)+'»</div>':'')+
  '<div class="word">'+esc(d.word)+'</div>'+
  '<div class="meta"><b>'+esc(d.lect_name||d.lect)+'</b> ('+d.lect+') · rama <b>'+esc(d.branch)+'</b>'+(d.subgroup?' / '+esc(d.subgroup):'')+' · '+esc(d.pos||'')+
    (d.is_loan?' · <span class="tag">préstamo</span>':'')+(d.is_proper?' · <span class="tag">propio</span>':'')+' · <span class="mut">fuente '+esc(d.source)+'</span></div>'+
  '<div class="sec">Sentidos'+(d.polyseme_links?' · '+d.polyseme_links+' enlaces de polisemia':'')+'</div>'+sens+
  ((d.concepts&&d.concepts.length)?'<div class="sec">Red de significado <span class="mut" style="font-weight:400;text-transform:none">(colexificación · todas las fuentes)</span></div>'+colex:'')+
  '<div class="sec">Etimología · toda la historia '+(d.reaches_pie?'<span class="pie">llega a PIE ✓</span>':(d.deepest?'<span class="mut" style="font-weight:400;text-transform:none">(hasta '+esc(d.deepest)+')</span>':''))+'</div>'+
    (d.etymology_text?'<div class="prose">'+esc(d.etymology_text)+'</div>':'')+
    (lin?'<div style="margin-top:6px">'+lin+'</div>':(d.etymology_text?'':'<span class="mut">—</span>'))+
  '<div class="sec">Cognados / coderivados</div>'+cogs+
  '<div class="sec">Fonética</div>'+
    '<div class="meta">IPA: '+(d.ipa_raw?'<code>'+esc(d.ipa_raw)+'</code> <span class="mut">fuente</span>':'')+
      (d.ipa_elab?' <code>'+esc(d.ipa_elab)+'</code> <span class="mut">G2P elaborada</span>':'')+(!d.ipa_raw&&!d.ipa_elab?'<span class="mut">— sin IPA</span>':'')+'</div>'+
    '<div style="margin-top:6px">'+segs+'</div>'+
  '<div class="sec">Análisis endolingüístico <span class="mut" style="font-weight:400;text-transform:none">(capa derivada · el código va sobre la RAÍZ)</span></div>'+endo;}
loadLects();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def _send(self, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(200); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path); qs = parse_qs(u.query)
        try:
            if u.path == "/":
                self._send(PAGE, "text/html; charset=utf-8")
            elif u.path == "/api/lects":
                self._send(json.dumps(lects(), ensure_ascii=False))
            elif u.path == "/api/search":
                self._send(json.dumps(search(qs.get("q", [""])[0], qs.get("lect", [""])[0]), ensure_ascii=False))
            elif u.path == "/api/concepts":
                self._send(json.dumps(concepts(qs.get("q", [""])[0]), ensure_ascii=False))
            elif u.path == "/api/concept":
                self._send(json.dumps(concept_forms(qs.get("id", [""])[0], qs.get("family", [""])[0]), ensure_ascii=False))
            elif u.path == "/api/form":
                self._send(json.dumps(detail(qs.get("id", [""])[0]), ensure_ascii=False))
            else:
                self.send_response(404); self.end_headers()
        except Exception as ex:
            self._send(json.dumps({"error": str(ex)}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Visor del corpus → http://localhost:{PORT}   (Ctrl-C para parar)")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
