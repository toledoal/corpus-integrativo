#!/usr/bin/env python3
"""Capa de NORMALIZACIÓN de datos — para escalar a fuentes y SCRIPTS heterogéneos (cirílico, devanagari, árabe…).

Dos ejes de heterogeneidad al crecer a miles de lenguas:

1) ESQUEMA de la fuente. Kaikki viene en dos formatos:
   - compacto  : {word, pos, ipa:[…], ety, ety_t:[{n,a}], gloss:[…]}
   - CRUDO wiktextract: {word, pos, sounds:[{ipa}], etymology_text, etymology_templates:[{name,args}], senses:[{glosses}]}
   `kaikki_entry(d)` devuelve SIEMPRE la forma compacta, venga de donde venga.

2) SISTEMA DE ESCRITURA (script). PRINCIPIO RECTOR: el esqueleto OAS sale del **IPA** (fonémico), que es
   INDEPENDIENTE del script — Hindi en devanagari, ruso en cirílico o alemán en latín dan esqueleto igual
   MIENTRAS Kaikki traiga IPA. El script solo importa en el *fallback ortográfico* (lenguas antiguas/proto sin
   IPA): ahí `detect_script()` enruta y `romanize()` translitera a latín las CONSONANTES (basta para la clase OAS,
   que es gruesa: labial/dental/velar/sibilante/líquida/nasal). Romanización best-effort sin dependencias.
"""
import unicodedata


# ─────────────────────────── 1) ESQUEMA ───────────────────────────
def kaikki_entry(d):
    """Normaliza una entrada Kaikki (compacta o cruda) → dict(word,pos,ipa,ety,ety_t,glosses)."""
    ety = d.get("ety") or d.get("etymology_text")
    ety_t = d.get("ety_t")
    if ety_t is None and d.get("etymology_templates"):
        ety_t = [{"n": t.get("name"), "a": t.get("args") or {}} for t in d["etymology_templates"]]
    ipa = d.get("ipa") or [s["ipa"] for s in (d.get("sounds") or []) if s.get("ipa")]
    gloss = d.get("gloss")
    if gloss is None:
        gloss = [g for s in (d.get("senses") or []) for g in (s.get("glosses") or [])]
    return {"word": d.get("word"), "pos": d.get("pos") or "x",
            "ipa": ipa, "ety": ety, "ety_t": ety_t or [], "glosses": gloss or []}


# ─────────────────────────── 2) SCRIPT ───────────────────────────
# rangos Unicode (inicio, fin, nombre) de los scripts que iremos encontrando
_RANGES = [
    (0x0041, 0x024F, "Latin"), (0x0370, 0x03FF, "Greek"), (0x0400, 0x04FF, "Cyrillic"),
    (0x0530, 0x058F, "Armenian"), (0x0590, 0x05FF, "Hebrew"), (0x0600, 0x06FF, "Arabic"),
    (0x0900, 0x097F, "Devanagari"), (0x0980, 0x09FF, "Bengali"), (0x0E00, 0x0E7F, "Thai"),
    (0x10A0, 0x10FF, "Georgian"), (0x3040, 0x30FF, "Kana"), (0x4E00, 0x9FFF, "Han"),
    (0xAC00, 0xD7AF, "Hangul"),
]


def detect_script(text):
    """Script dominante de una cadena (por la 1ª letra clasificable). 'Latin' por defecto/desconocido."""
    for ch in text or "":
        if not ch.isalpha():
            continue
        cp = ord(ch)
        for lo, hi, name in _RANGES:
            if lo <= cp <= hi:
                return name
    return "Latin"


# romanización de CONSONANTES por script (suficiente para la clase OAS; vocales aproximadas).
_CYR = {"б":"b","п":"p","в":"v","ф":"f","м":"m","н":"n","т":"t","д":"d","с":"s","з":"z","ц":"ts",
        "ч":"ch","ш":"sh","щ":"sh","ж":"zh","к":"k","г":"g","х":"kh","л":"l","р":"r","й":"j",
        "ґ":"g","ђ":"dj","ћ":"c","џ":"dzh","љ":"l","њ":"n","ј":"j","а":"a","е":"e","и":"i","і":"i",
        "о":"o","у":"u","ы":"y","э":"e","ю":"ju","я":"ja","ё":"jo","є":"je","ї":"ji","ъ":"","ь":""}
_GRK = {"β":"b","π":"p","φ":"f","μ":"m","ν":"n","τ":"t","δ":"d","θ":"th","σ":"s","ς":"s","ζ":"z",
        "κ":"k","γ":"g","χ":"kh","λ":"l","ρ":"r","ξ":"ks","ψ":"ps","α":"a","ε":"e","η":"e","ι":"i",
        "ο":"o","υ":"u","ω":"o"}
# Devanagari: abugida (vocal inherente 'a'). Consonantes + vocales independientes + signos.
_DEV = {# consonantes
        "क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"n","च":"ch","छ":"ch","ज":"j","झ":"jh","ञ":"n",
        "ट":"t","ठ":"th","ड":"d","ढ":"dh","ण":"n","त":"t","थ":"th","द":"d","ध":"dh","न":"n",
        "प":"p","फ":"f","ब":"b","भ":"bh","म":"m","य":"j","र":"r","ल":"l","ळ":"l","व":"v",
        "श":"sh","ष":"sh","स":"s","ह":"h",
        "क़":"k","ख़":"kh","ग़":"g","ज़":"z","ड़":"r","ढ़":"r","फ़":"f","य़":"j",           # con nukta
        # vocales INDEPENDIENTES (aparecen a inicio de palabra)
        "अ":"a","आ":"a","इ":"i","ई":"i","उ":"u","ऊ":"u","ऋ":"r","ॠ":"r","ऌ":"l","ए":"e","ऐ":"e",
        "ओ":"o","औ":"o","ऑ":"o",
        # signos dependientes de vocal (matras)
        "ा":"a","ि":"i","ी":"i","ु":"u","ू":"u","ृ":"r","े":"e","ै":"e","ो":"o","ौ":"o","ऽ":""}
# Armenio (para Old/Middle Armenian sin IPA; el moderno hy va por IPA). APROX declarada: los africados
# ts/dz/č/ǰ (ծ ց ձ ճ չ ջ) se colapsan a 's' (Σ, release sibilante) — cobertura, no decisión OAS fina.
_ARM = {"ա":"a","բ":"b","գ":"g","դ":"d","ե":"e","զ":"z","է":"e","ը":"","թ":"t","ժ":"z","ի":"i",
        "լ":"l","խ":"x","ծ":"s","կ":"k","հ":"h","ձ":"s","ղ":"r","ճ":"s","մ":"m","յ":"y","ն":"n",
        "շ":"s","ո":"o","չ":"s","պ":"p","ջ":"s","ռ":"r","ս":"s","վ":"v","տ":"t","ր":"r","ց":"s",
        "ւ":"w","փ":"p","ք":"k","օ":"o","ֆ":"f","և":"ev"," և":"ev"}
_MAPS = {"Cyrillic": _CYR, "Greek": _GRK, "Devanagari": _DEV, "Armenian": _ARM}
_ALL = {**_CYR, **_GRK, **_DEV, **_ARM}             # mapa combinado (para formas de script MEZCLADO)


def romanize(text, script=None):
    """Translitera best-effort a latín para el fallback ortográfico, CHAR POR CHAR con el mapa combinado:
    el latín pasa tal cual y cualquier carácter no-latino embebido (script mezclado) se mapea. Si el script
    DOMINANTE no tiene mapa aún (árabe/han/hangul…), devuelve '' (declara el hueco, no inventa)."""
    script = script or detect_script(text)
    if script != "Latin" and _MAPS.get(script) is None:
        return ""                                   # script sin soporte → pendiente
    out = []
    for ch in unicodedata.normalize("NFC", text or ""):
        if unicodedata.category(ch).startswith("M"):
            continue                                # marca combinante (acento/tono) → fuera
        out.append(_ALL.get(ch.lower(), ch))        # no-latino mapeado; latino pasa
    return "".join(out)
