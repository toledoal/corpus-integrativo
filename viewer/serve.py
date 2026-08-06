#!/usr/bin/env python3
"""Visor super simple del corpus — busca una palabra y muestra TODAS sus capas por entrada.

Servidorcito local (stdlib http.server + psycopg): consulta Postgres y sirve una página con buscador.
Ver de verdad qué obtenemos por forma: grafía → IPA (fuente/G2P) → segmentos → esqueleto → código OAS →
vocales/CV → sentidos → etimología → cognados (con sus reflejos) → firma crypto.

Uso:  .venv/bin/python viewer/serve.py     →  abrir http://localhost:8080
"""
import json
import sys
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingest"))
import psycopg
from config import DSN

PORT = int(os.environ.get("CI_VIEWER_PORT", "8080"))


def db():
    return psycopg.connect(DSN)


def search(q, lect):
    with db() as c, c.cursor() as cur:
        if lect:
            cur.execute("SELECT id, lect_id, orthography FROM form WHERE lower(orthography)=lower(%s) AND lect_id=%s "
                        "AND source_id='kaikki' LIMIT 60", (q, lect))
        else:
            cur.execute("SELECT id, lect_id, orthography FROM form WHERE lower(orthography)=lower(%s) "
                        "AND source_id='kaikki' LIMIT 60", (q,))
        rows = cur.fetchall()
        if not rows:   # fallback: prefijo
            cur.execute("SELECT id, lect_id, orthography FROM form WHERE lower(orthography) LIKE lower(%s) "
                        "AND source_id='kaikki' LIMIT 60", (q + "%",))
            rows = cur.fetchall()
        return [{"id": r[0], "lect": r[1], "word": r[2]} for r in rows]


def detail(fid):
    with db() as c, c.cursor() as cur:
        cur.execute("""SELECT f.lect_id, f.orthography, f.ipa_raw, f.ipa_elab, f.pos, f.etymology_text,
                       f.is_proper, f.source_id, l.name, l.family, l.subgroup
                       FROM form f LEFT JOIN lect l ON l.id=f.lect_id WHERE f.id=%s""", (fid,))
        r = cur.fetchone()
        if not r:
            return {"error": "no encontrado"}
        d = {"id": fid, "lect": r[0], "lect_name": r[8], "family": r[9], "subgroup": r[10],
             "word": r[1], "ipa_raw": r[2], "ipa_elab": r[3], "pos": r[4], "etymology_text": r[5],
             "is_proper": r[6], "source": r[7]}
        cur.execute("SELECT ipa, syllable, is_stressed FROM segment WHERE form_id=%s ORDER BY pos", (fid,))
        d["segments"] = [{"ipa": s[0], "syl": s[1], "stress": s[2]} for s in cur.fetchall()]
        cur.execute("SELECT cons_skeleton, code, core_skeleton, vowels, cv_template, is_compound FROM skeleton WHERE form_id=%s", (fid,))
        s = cur.fetchone()
        d["skeleton"] = ({"cons": s[0], "code": s[1], "core": s[2], "vowels": s[3], "cv": s[4], "compound": s[5]} if s else None)
        cur.execute("SELECT gloss FROM sense WHERE form_id=%s AND gloss IS NOT NULL LIMIT 20", (fid,))
        d["senses"] = [g[0] for g in cur.fetchall()]
        cur.execute("SELECT parent_lect, parent_form, kind FROM form_etymology WHERE child_form_id=%s ORDER BY id", (fid,))
        d["etymology"] = [{"lect": e[0], "form": e[1], "kind": e[2]} for e in cur.fetchall()]
        cur.execute("SELECT self_info FROM crypto WHERE form_id=%s", (fid,))
        cy = cur.fetchone()
        d["self_info"] = float(cy[0]) if cy and cy[0] is not None else None
        # cognados: sets a los que pertenece + otros reflejos
        cur.execute("""SELECT cs.id, cs.label, cs.family, cs.ancestor_lect FROM cognate_member cm
                       JOIN cognate_set cs ON cs.id=cm.cognate_set_id WHERE cm.form_id=%s""", (fid,))
        d["cognate_sets"] = []
        for cs_id, label, fam, anc in cur.fetchall():
            cur.execute("""SELECT f.lect_id, f.orthography, sk.code FROM cognate_member cm
                           JOIN form f ON f.id=cm.form_id LEFT JOIN skeleton sk ON sk.form_id=f.id
                           WHERE cm.cognate_set_id=%s ORDER BY f.lect_id LIMIT 40""", (cs_id,))
            members = [{"lect": m[0], "word": m[1], "code": m[2]} for m in cur.fetchall()]
            d["cognate_sets"].append({"id": cs_id, "label": label, "family": fam, "ancestor": anc, "members": members})
        return d


PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Corpus Integrativo · visor</title>
<style>
 :root{--bg:#faf9f6;--fg:#1a1a1a;--mut:#6b6b6b;--acc:#8a5a2b;--card:#fff;--line:#e6e2da;--code:#f0ece3}
 @media(prefers-color-scheme:dark){:root{--bg:#17150f;--fg:#eae6dc;--mut:#9c968a;--acc:#d9a566;--card:#211e17;--line:#332e24;--code:#26221a}}
 *{box-sizing:border-box}body{margin:0;font:15px/1.5 ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--fg)}
 header{padding:14px 20px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:2}
 h1{font-size:16px;margin:0 0 8px;font-weight:600;letter-spacing:.02em}h1 span{color:var(--acc)}
 .search{display:flex;gap:8px;max-width:640px}
 input{flex:1;padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font-size:15px}
 input.lect{flex:0 0 90px}button{padding:9px 16px;border:0;border-radius:8px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer}
 main{display:grid;grid-template-columns:230px 1fr;gap:0;min-height:calc(100vh - 64px)}
 #results{border-right:1px solid var(--line);overflow:auto;max-height:calc(100vh - 64px)}
 .r{padding:9px 16px;border-bottom:1px solid var(--line);cursor:pointer}.r:hover{background:var(--code)}.r.sel{background:var(--code);border-left:3px solid var(--acc)}
 .r b{font-weight:600}.r .lc{color:var(--mut);font-size:12px;margin-left:6px}
 #detail{padding:20px 26px;overflow:auto;max-height:calc(100vh - 64px)}
 .word{font-size:30px;font-weight:700}.word .lc{font-size:14px;color:var(--mut);font-weight:400;margin-left:10px}
 .code{font-size:26px;color:var(--acc);letter-spacing:.06em;margin:6px 0 2px}
 .row{display:flex;gap:10px;padding:7px 0;border-bottom:1px solid var(--line)}.row .k{flex:0 0 130px;color:var(--mut);font-size:13px;text-transform:uppercase;letter-spacing:.04em}
 .k2{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin:18px 0 6px}
 code,.mono{font-family:ui-monospace,monospace;background:var(--code);padding:1px 6px;border-radius:5px}
 .seg{display:inline-block;padding:3px 8px;margin:2px;border:1px solid var(--line);border-radius:6px;font-family:ui-monospace,monospace}
 .seg.st{border-color:var(--acc);color:var(--acc);font-weight:700}
 .tag{display:inline-block;padding:1px 7px;border-radius:20px;background:var(--code);font-size:12px;margin-right:6px}
 table{border-collapse:collapse;width:100%;margin:4px 0}td{padding:4px 8px;border-bottom:1px solid var(--line);font-size:14px}
 td.lc{color:var(--mut);width:56px}td.cd{font-family:ui-monospace,monospace;color:var(--acc)}
 .cog{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0;background:var(--card)}
 .cog h4{margin:0 0 6px;font-size:13px}.mut{color:var(--mut)}.hint{color:var(--mut);padding:40px 26px}
</style></head><body>
<header><h1>Corpus Integrativo · <span>visor por entrada</span></h1>
 <form class="search" onsubmit="return go(event)">
  <input id="q" placeholder="palabra (grafía original, cualquier script)…" autofocus>
  <input id="lc" class="lect" placeholder="lect">
  <button>Buscar</button></form></header>
<main><div id="results"></div><div id="detail"><div class="hint">Busca una palabra para ver todas sus capas.</div></div></main>
<script>
async function go(e){e&&e.preventDefault();const q=document.getElementById('q').value.trim();const lc=document.getElementById('lc').value.trim();
 if(!q)return false;const rs=await (await fetch('/api/search?q='+encodeURIComponent(q)+'&lect='+encodeURIComponent(lc))).json();
 const R=document.getElementById('results');R.innerHTML=rs.length?'':'<div class="hint">sin resultados</div>';
 rs.forEach(r=>{const d=document.createElement('div');d.className='r';d.innerHTML='<b>'+esc(r.word)+'</b><span class="lc">'+r.lect+'</span>';
  d.onclick=()=>{[...R.children].forEach(x=>x.classList.remove('sel'));d.classList.add('sel');show(r.id);};R.appendChild(d);});
 if(rs.length)R.firstChild.click();return false;}
function esc(s){return (s==null?'':''+s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
async function show(id){const d=await (await fetch('/api/form?id='+encodeURIComponent(id))).json();const D=document.getElementById('detail');
 const sk=d.skeleton||{};
 let segs=(d.segments||[]).map(s=>'<span class="seg'+(s.stress?' st':'')+'">'+esc(s.ipa)+'</span>').join('');
 let sen=(d.senses||[]).map(g=>'<div>• '+esc(g)+'</div>').join('')||'<span class="mut">—</span>';
 let ety=(d.etymology||[]).map(e=>'<span class="tag">'+esc(e.kind||'')+'</span> '+esc(e.lect)+' <i>'+esc(e.form)+'</i>').join('<br>')||'<span class="mut">—</span>';
 let cogs=(d.cognate_sets||[]).map(cs=>'<div class="cog"><h4>'+esc(cs.label||cs.id)+' <span class="mut">· '+esc(cs.family)+(cs.ancestor?' · anc '+esc(cs.ancestor):'')+'</span></h4>'+
   '<table>'+cs.members.map(m=>'<tr><td class="lc">'+m.lect+'</td><td>'+esc(m.word)+'</td><td class="cd">'+esc(m.code||'')+'</td></tr>').join('')+'</table></div>').join('')||'<span class="mut">no está en ningún cognado</span>';
 D.innerHTML='<div class="word">'+esc(d.word)+'<span class="lc">'+esc(d.lect_name||d.lect)+' ('+d.lect+')'+(d.family?' · '+esc(d.family):'')+(d.subgroup?' / '+esc(d.subgroup):'')+'</span></div>'+
  (sk.code?'<div class="code">'+esc(sk.code)+'</div>':'')+
  '<div class="row"><div class="k">IPA</div><div>'+(d.ipa_raw?'<code>'+esc(d.ipa_raw)+'</code> <span class="mut">fuente</span>':'')+
     (d.ipa_elab?' <code>'+esc(d.ipa_elab)+'</code> <span class="mut">G2P</span>':'')+(!d.ipa_raw&&!d.ipa_elab?'<span class="mut">— sin IPA</span>':'')+'</div></div>'+
  '<div class="row"><div class="k">esqueleto</div><div><code>'+esc(sk.cons||'—')+'</code>'+(sk.core?' · núcleo <code>'+esc(sk.core)+'</code>':'')+(sk.compound?' <span class="tag">compuesto</span>':'')+'</div></div>'+
  '<div class="row"><div class="k">vocales / CV</div><div><code>'+esc(sk.vowels||'—')+'</code> · <code>'+esc(sk.cv||'—')+'</code></div></div>'+
  '<div class="row"><div class="k">pos / crypto</div><div>'+esc(d.pos||'—')+(d.self_info!=null?' · self-info <code>'+d.self_info.toFixed(2)+'</code>':'')+(d.is_proper?' · <span class="tag">propio</span>':'')+'</div></div>'+
  '<div class="k2">segmentos ('+(d.segments||[]).length+')</div><div>'+(segs||'<span class="mut">—</span>')+'</div>'+
  '<div class="k2">sentidos</div>'+sen+
  '<div class="k2">etimología</div><div>'+ety+'</div>'+
  '<div class="k2">cognados / coderivados</div>'+cogs;}
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
            elif u.path == "/api/search":
                self._send(json.dumps(search(qs.get("q", [""])[0], qs.get("lect", [""])[0])))
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
