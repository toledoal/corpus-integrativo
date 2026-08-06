#!/usr/bin/env python3
"""PRE-FLIGHT — inspecciona archivos Kaikki ANTES de cargarlos y reporta qué funcionará y qué falta.

Mide, sin tocar la BD, las cosas que suelen romper al añadir una familia nueva:
  - ESQUEMA de la fuente (compacto vs crudo wiktextract)
  - cobertura de IPA (capa 2 del pipeline: palabra → IPA → esqueleto → OAS)
  - SCRIPTS presentes en las grafías (¿latín, devanagari, perso-árabe…?)
  - símbolos IPA que NUESTRO mapeo OAS aún NO clasifica (los futuros '?')
  - cobertura de etimología y glosas
Así sabemos el esfuerzo (¿hace falta G2P? ¿ampliar OAS?) con datos, no en teoría.

Uso: .venv/bin/python ingest/preflight.py Hindi Urdu [--sample 4000]
"""
import argparse, json, os, unicodedata
from collections import Counter
from config import KDIR
import normalize
from recompute_skeleton import IPA, VOW, GLI, IGNORE, BOUNDARY, _clean, seg_class_char
from segment_kaikki import segment as seg_ipa


def unclassifiable(ipa_str):
    """símbolos de una cadena IPA que NO caen en consonante-clase / glide / vocal / ignore → futuros '?'."""
    bad = []
    for s, _syl, _st in seg_ipa(ipa_str):
        base = _clean(s)
        if not base or set(base) <= BOUNDARY or set(base) <= IGNORE:
            continue
        if seg_class_char(s) or any(c in GLI for c in base) or any(c in VOW for c in base):
            continue
        bad.append(s)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("languages", nargs="+")
    ap.add_argument("--sample", type=int, default=4000)
    args = ap.parse_args()

    for lang in args.languages:
        path = os.path.join(KDIR, f"{lang}.jsonl")
        if not os.path.isfile(path):
            print(f"\n### {lang}: !! no existe {path}"); continue
        n = with_ipa = with_ety = with_gloss = raw_schema = 0
        scripts = Counter(); badsyms = Counter()
        for i, line in enumerate(open(path, encoding="utf-8")):
            if i >= args.sample:
                break
            d = json.loads(line)
            if d.get("sounds") or d.get("etymology_text") or d.get("senses"):
                raw_schema += 1
            e = normalize.kaikki_entry(d)
            n += 1
            if e["word"]:
                scripts[normalize.detect_script(e["word"])] += 1
            if e["ipa"]:
                with_ipa += 1
                badsyms.update(unclassifiable(e["ipa"][0]))
            if e["ety"] or e["ety_t"]:
                with_ety += 1
            if e["glosses"]:
                with_gloss += 1
        pct = lambda x: f"{100*x/max(1,n):.0f}%"
        print(f"\n### {lang}  (muestra {n})")
        print(f"  esquema      : {'CRUDO wiktextract' if raw_schema > n/2 else 'compacto'}")
        print(f"  con IPA      : {pct(with_ipa)}   ← capa 2 (esqueleto sale de aquí)")
        print(f"  con etimología: {pct(with_ety)}   con glosa: {pct(with_gloss)}")
        print(f"  scripts      : " + ", ".join(f"{s} {pct(c)}" for s, c in scripts.most_common()))
        if badsyms:
            top = ", ".join(f"'{s}'×{c}" for s, c in badsyms.most_common(12))
            print(f"  IPA sin clasificar (futuros '?'): {len(badsyms)} tipos → {top}")
        else:
            print(f"  IPA sin clasificar: NINGUNO ✓ (el mapeo OAS actual cubre este inventario)")
        # veredicto simple
        if with_ipa < n * 0.5:
            print(f"  ⇒ VEREDICTO: IPA escasa ({pct(with_ipa)}) → hará falta ELABORAR IPA (G2P) para {lang}.")
        elif badsyms:
            print(f"  ⇒ VEREDICTO: IPA OK, pero ampliar OAS con {len(badsyms)} símbolos antes de cargar.")
        else:
            print(f"  ⇒ VEREDICTO: carga limpia esperable (IPA suficiente + OAS cubre el inventario).")


if __name__ == "__main__":
    main()
