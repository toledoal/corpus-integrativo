#!/usr/bin/env python3
"""Decomposición morfológica POR ETIMOLOGÍA (honesta, con fuente) → un código endolingüístico POR MORFEMA.

Corrige el error de fondo: el código se calculaba sobre la forma superficial fusionada (aleshores → Λ·Σ·Λ·Σ),
cuando lo que importa es la RAÍZ (aleshores < ad illās hōrās → raíz = hōrās). Aquí, usando SOLO lo que la
etimología ya dice (no inventamos raíces por reglas de flexión), se parte la palabra en morfemas y se marca cuál
es la raíz. Cada morfema recibe su esqueleto y su código; la raíz alimenta `skeleton.core_skeleton`.

Dos casos, ambos con fuente:
  · CASO A — etymology_text con cadena explícita "From X + Y [+ Z]" (Wiktionary ya segmenta: "semi- + formale",
    "metafora + -ismo"). Afijo = lleva guion inicial/final; RAÍZ = el componente sin guion (la cabeza de contenido).
  · CASO B — form_etymology.parent_form multipalabra ("ad illās hōrās"): univerbación de una frase. La RAÍZ es la
    cabeza de contenido (último token); los determinantes/preposiciones quedan como afijos de función.

Escribe morph(role,gloss,surface,code,cons_skeleton,morph_ord,source_id='etymology-decomp') y actualiza
skeleton.core_skeleton (raíz) + is_compound. NO toca las morph de otra fuente (affix_extract). Idempotente.

Uso: .venv/bin/python ingest/decompose_morphemes.py [lect …]   (sin args = todos los kaikki)
"""
import re
import sys
import psycopg
from config import DSN
from recompute_skeleton import compute, SYM
from skeleton_from_ortho import ortho_segments

SRC = "etymology-decomp"
# preposiciones/determinantes que son FUNCIÓN, no raíz (latín/romance) — para elegir la cabeza en el caso B
FUNCS = {"ad", "de", "in", "ex", "ex-", "per", "cum", "ab", "ob", "sub", "a", "e", "et", "il", "el", "la", "le",
         "lo", "los", "las", "les", "un", "una", "y", "i", "ille", "illa", "illud", "illās", "illas", "illos",
         "illōs", "illa", "ipse", "ipsa", "hoc", "hic", "se", "non", "ne", "que", "of", "the", "at", "to"}
_PARENS = re.compile(r"\([^)]*\)")
_QUOTES = re.compile(r'[“”"\'‘’]')
_LEAD = re.compile(r"^\s*(?:inherited\s+from|from|univerbation of|compound of|contraction of|blend of|"
                   r"clipping of|abbreviation of|by univerbation of|calque of|borrowed from)\s+", re.I)


def clean_morph(tok):
    """limpia un componente de la etimología → string de morfema (conserva guion que marca afijo)."""
    tok = _QUOTES.sub("", _PARENS.sub("", tok)).strip()
    tok = re.sub(r"[\.,;:]+$", "", tok).strip()
    tok = re.sub(r"\s+", " ", tok)
    return tok


def morph_code(s):
    """string de morfema → (cons_skeleton, code) por el esqueletizador ortográfico (mismo compute)."""
    segs = ortho_segments(s.replace("-", ""))
    if not segs:
        return None, None
    cons, code, *_ = compute(segs)
    return cons, code


def parse_plus(etytext):
    """CASO A: extrae la cadena 'X + Y + Z' del etymology_text. Devuelve lista de morfemas o None."""
    if not etytext or " + " not in etytext:
        return None
    # la oración que contiene el ' + '
    sent = next((s for s in re.split(r"(?<=[\.\n])\s+", etytext) if " + " in s), None)
    if not sent:
        return None
    sent = _PARENS.sub("", sent)
    sent = _LEAD.sub("", sent).strip()
    parts = [clean_morph(p) for p in sent.split(" + ")]
    parts = [p for p in parts if p and len(p) <= 30 and re.match(r"^[\wÀ-ɏ\- ]+$", p)]
    return parts if len(parts) >= 2 else None


def is_affix(m):
    return m.startswith("-") or m.endswith("-")


def decompose(etytext, parent_form):
    """→ (morfemas, idx_raiz, is_compound) o None. morfemas = [(surface, role)]."""
    # CASO A: derivación/compuesto explícito con ' + '
    parts = parse_plus(etytext)
    if parts:
        roles = ["affix" if is_affix(p) else "root" for p in parts]
        roots = [i for i, r in enumerate(roles) if r == "root"]
        if not roots:
            return None
        idx = roots[-1]                              # cabeza = último componente de contenido
        return [(p, r) for p, r in zip(parts, roles)], idx, len(roots) >= 2
    # CASO B: etymon multipalabra (univerbación de frase: 'ad illās hōrās')
    if parent_form and " " in parent_form.strip():
        toks = [t for t in re.split(r"\s+", parent_form.strip().strip("*")) if t]
        if len(toks) < 2 or len(toks) > 5:
            return None
        roles = ["affix" if t.lower().strip("-") in FUNCS else "root" for t in toks]
        roots = [i for i, r in enumerate(roles) if r == "root"]
        if not roots:                                # todo función: la cabeza es el último token igual
            roles[-1] = "root"; roots = [len(toks) - 1]
        idx = roots[-1]                              # cabeza de contenido = último
        return [(t, r) for t, r in zip(toks, roles)], idx, True
    return None


def main():
    want = sys.argv[1:]
    conn = psycopg.connect(DSN); cur = conn.cursor()

    # borrar decomposición previa nuestra (no toca affix_extract)
    cur.execute("DELETE FROM morph WHERE source_id=%s", (SRC,)); conn.commit()

    # formas con etimología y SIN morph previa (no peleamos con affix_extract)
    q = """SELECT f.id, f.orthography, f.etymology_text, fe.parent_form
             FROM form f
             LEFT JOIN LATERAL (SELECT parent_form FROM form_etymology e
                                WHERE e.child_form_id=f.id AND e.kind='herencia' LIMIT 1) fe ON true
            WHERE f.source_id='kaikki' AND f.etymology_text IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM morph m WHERE m.form_id=f.id)"""
    if want:
        q += " AND f.lect_id = ANY(%s)"
        cur.execute(q, (want,))
    else:
        cur.execute(q)
    rows = cur.fetchall()
    print(f"formas candidatas (con etimología, sin morph): {len(rows):,}")

    morph_rows, core_upd = [], []
    ncompound = ndecomp = 0
    for fid, orth, etytext, parent in rows:
        res = decompose(etytext, parent)
        if not res:
            continue
        morphs, idx, compound = res
        root_surface = morphs[idx][0]
        rcons, rcode = morph_code(root_surface)
        if not rcode:                                # la raíz no da código → no aporta, se salta
            continue
        ndecomp += 1
        ncompound += int(compound)
        for o, (surface, role) in enumerate(morphs):
            cons, code = morph_code(surface)
            morph_rows.append((fid, role, surface, surface, cons, code, o, SRC))
        core_upd.append((fid, rcons, compound))

    # escribir morph
    with cur.copy("COPY morph(form_id,role,gloss,surface,cons_skeleton,code,morph_ord,source_id) FROM STDIN") as cp:
        for r in morph_rows:
            cp.write_row(r)
    # actualizar skeleton.core_skeleton (raíz) + is_compound
    cur.execute("CREATE TEMP TABLE _c(form_id TEXT, core TEXT, comp BOOL) ON COMMIT DROP")
    with cur.copy("COPY _c(form_id,core,comp) FROM STDIN") as cp:
        for r in core_upd:
            cp.write_row(r)
    cur.execute("UPDATE skeleton s SET core_skeleton=_c.core, is_compound=_c.comp FROM _c WHERE s.form_id=_c.form_id")
    conn.commit()

    print(f"OK · formas decompuestas={ndecomp:,} · morfemas={len(morph_rows):,} · compuestas/univerbadas={ncompound:,}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
