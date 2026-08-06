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
        cur.execute("SELECT parent_lect, parent_form, kind FROM form_etymology WHERE child_form_id=%s ORDER BY id", (fid,))
        d["etymology"] = [{"lect": e[0], "form": e[1], "kind": e[2]} for e in cur.fetchall()]
        cur.execute("""SELECT cs.id, cs.label, cs.source, cs.family FROM cognate_member cm
                       JOIN cognate_set cs ON cs.id=cm.cognate_set_id WHERE cm.form_id=%s""", (fid,))
        d["cognate_sets"] = []
        for cs_id, label, source, fam in cur.fetchall():
            cur.execute("""SELECT DISTINCT ON (f.lect_id, lower(f.orthography))
                           f.lect_id, f.orthography, (SELECT gloss FROM sense s WHERE s.form_id=f.id LIMIT 1)
                           FROM cognate_member cm JOIN form f ON f.id=cm.form_id
                           WHERE cm.cognate_set_id=%s ORDER BY f.lect_id, lower(f.orthography) LIMIT 60""", (cs_id,))
            mem = [{"lect": m[0], "word": m[1], "gloss": m[2]} for m in cur.fetchall()]
            d["cognate_sets"].append({"label": label, "source": source, "family": fam, "members": mem})
        # análisis (secundario)
        cur.execute("SELECT cons_skeleton, code, core_skeleton, vowels, cv_template FROM skeleton WHERE form_id=%s", (fid,))
        s = cur.fetchone()
        d["skeleton"] = ({"cons": s[0], "code": s[1], "core": s[2], "vowels": s[3], "cv": s[4]} if s else None)
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
 td.lc{color:var(--mut);width:52px}td.gl{color:var(--mut)}
 .seg{display:inline-block;padding:2px 7px;margin:2px;border:1px solid var(--line);border-radius:6px;font-family:ui-monospace,monospace}
 .seg.st{border-color:var(--acc);color:var(--acc);font-weight:700}
 .anal{background:var(--soft);border-radius:8px;padding:12px 14px;margin-top:6px;font-size:13px;color:var(--mut)}
 .anal code{background:var(--card)}.anal .lbl{color:var(--mut);text-transform:uppercase;font-size:11px;letter-spacing:.04em}
 .mut{color:var(--mut)}.hint{color:var(--mut);padding:42px 30px}
</style></head><body>
<header><h1>Corpus <b>Integrativo</b></h1>
 <form onsubmit="return go(event)" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
  <input id="q" placeholder="palabra (cualquier alfabeto)…" autofocus>
  <select id="lc"><option value="">— todas las lenguas —</option></select>
  <button>Buscar</button></form>
 <span id="branchinfo" class="mut" style="font-size:13px"></span></header>
<main><div id="results"></div><div id="detail"><div class="hint">Busca una palabra para ver toda su información.</div></div></main>
<script>
let LECTS={};
async function loadLects(){const ls=await (await fetch('/api/lects')).json();const sel=document.getElementById('lc');
 ls.forEach(l=>{LECTS[l.id]=l;const o=document.createElement('option');o.value=l.id;
  o.textContent=l.name+' — '+l.branch+(l.subgroup?' / '+l.subgroup:'')+' ('+l.n+')';sel.appendChild(o);});}
document.getElementById('lc')?.addEventListener('change',e=>{const l=LECTS[e.target.value];
 document.getElementById('branchinfo').textContent=l?('rama: '+l.branch+(l.subgroup?' · '+l.subgroup:'')+' · '+l.n+' formas'):'';});
function esc(s){return (s==null?'':''+s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
async function go(e){e&&e.preventDefault();const q=document.getElementById('q').value.trim();const lc=document.getElementById('lc').value;
 if(!q)return false;const rs=await (await fetch('/api/search?q='+encodeURIComponent(q)+'&lect='+encodeURIComponent(lc))).json();
 const R=document.getElementById('results');R.innerHTML=rs.length?'':'<div class="hint">sin resultados</div>';
 rs.forEach(r=>{const d=document.createElement('div');d.className='r';d.innerHTML='<b>'+esc(r.word)+'</b><span class="lc">'+r.lect+'</span>';
  d.onclick=()=>{[...R.children].forEach(x=>x.classList.remove('sel'));d.classList.add('sel');show(r.id);};R.appendChild(d);});
 if(rs.length)R.firstChild.click();return false;}
async function show(id){const d=await (await fetch('/api/form?id='+encodeURIComponent(id))).json();const D=document.getElementById('detail');
 const sk=d.skeleton||{};
 let sens=(d.senses||[]).map((g,i)=>'<div class="sens"><span class="n">'+(i+1)+'.</span>'+esc(g)+'</div>').join('')||'<span class="mut">—</span>';
 let lin=(d.etymology||[]).map(e=>'<div class="lin"><span class="kind">'+esc(e.kind||'')+'</span>'+esc(e.lect)+' <i>'+esc(e.form)+'</i></div>').join('');
 let cogs=(d.cognate_sets||[]).map(cs=>'<div class="cog"><h4>'+esc(cs.label||'')+' <span class="src">· '+esc(cs.source)+(cs.family?' · '+esc(cs.family):'')+'</span></h4>'+
   '<table>'+cs.members.map(m=>'<tr><td class="lc">'+m.lect+'</td><td>'+esc(m.word)+'</td><td class="gl">'+esc(m.gloss||'')+'</td></tr>').join('')+'</table></div>').join('')||'<span class="mut">no ligado a cognados aún</span>';
 let segs=(d.segments||[]).map(s=>'<span class="seg'+(s.stress?' st':'')+'">'+esc(s.ipa)+'</span>').join('')||'<span class="mut">—</span>';
 D.innerHTML='<div class="word">'+esc(d.word)+'</div>'+
  '<div class="meta"><b>'+esc(d.lect_name||d.lect)+'</b> ('+d.lect+') · rama <b>'+esc(d.branch)+'</b>'+(d.subgroup?' / '+esc(d.subgroup):'')+' · '+esc(d.pos||'')+
    (d.is_loan?' · <span class="tag">préstamo</span>':'')+(d.is_proper?' · <span class="tag">propio</span>':'')+' · <span class="mut">fuente '+esc(d.source)+'</span></div>'+
  '<div class="sec">Sentidos'+(d.polyseme_links?' · '+d.polyseme_links+' enlaces de polisemia':'')+'</div>'+sens+
  '<div class="sec">Etimología (historia)</div>'+
    (d.etymology_text?'<div class="prose">'+esc(d.etymology_text)+'</div>':'')+
    (lin?'<div style="margin-top:6px">'+lin+'</div>':(d.etymology_text?'':'<span class="mut">—</span>'))+
  '<div class="sec">Cognados / coderivados</div>'+cogs+
  '<div class="sec">Fonética</div>'+
    '<div class="meta">IPA: '+(d.ipa_raw?'<code>'+esc(d.ipa_raw)+'</code> <span class="mut">fuente</span>':'')+
      (d.ipa_elab?' <code>'+esc(d.ipa_elab)+'</code> <span class="mut">G2P elaborada</span>':'')+(!d.ipa_raw&&!d.ipa_elab?'<span class="mut">— sin IPA</span>':'')+'</div>'+
    '<div style="margin-top:6px">'+segs+'</div>'+
  '<div class="sec">Análisis endolingüístico <span class="mut" style="font-weight:400;text-transform:none">(capa derivada)</span></div>'+
    '<div class="anal"><span class="lbl">esqueleto</span> <code>'+esc(sk.cons||'—')+'</code>'+(sk.core?' · <span class="lbl">núcleo</span> <code>'+esc(sk.core)+'</code>':'')+
     ' · <span class="lbl">código OAS</span> <code>'+esc(sk.code||'—')+'</code> · <span class="lbl">vocales</span> <code>'+esc(sk.vowels||'—')+'</code>'+
     (d.self_info!=null?' · <span class="lbl">self-info</span> <code>'+d.self_info.toFixed(2)+'</code>':'')+'</div>';}
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
