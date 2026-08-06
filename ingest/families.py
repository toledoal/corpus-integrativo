#!/usr/bin/env python3
"""Registro de SUBSISTEMAS de lenguas — centraliza todo lo específico de familia para que el pipeline replique.

Cada builder lee la familia ACTIVA vía la variable de entorno CI_FAMILY (default 'romance') y usa:
  - members  : los lects del subsistema (el pipeline SOLO toca estos)
  - ancestors: niveles de ancestro por prioridad, cada uno (etiqueta, [lects-padre], status) — para etymon/protoforma
               status ∈ {'atestiguado','reconstruido'} (latín está atestiguado; los proto-* se reconstruyen)
  - kaikki_files  : nombre-de-archivo/lengua Kaikki → código de lect (para el loader)
  - reconcile_pairs: glottocode → iso (para fusionar nodos duplicados de lengua)

Replicar a otra familia = definir su entrada aquí y correr:  CI_FAMILY=germanic ./ingest/build_analytics.sh
NO se aplica ninguna familia salvo la que se pida; definirla aquí NO toca datos.
"""
import os

FAMILIES = {
    # ───────────────────────── ROMANCE (piloto COMPLETO) ─────────────────────────
    "romance": {
        "members": ["la", "es", "it", "fr", "pt", "ca", "ro", "gl", "oc", "sc",
                    "scn", "nap", "rup", "fur", "lld", "wa", "fro", "osp"],
        # cada nivel = UNA lengua ancestro (sus variantes comparten clave). Proto-Itálico y PIE son
        # lenguas DISTINTAS → niveles separados (no se funden). Orden = prioridad (ancestro más cercano primero).
        "ancestors": [
            # TODAS las variedades de latín colapsan a la clave 'la' (misma lengua) para NO fragmentar cognación;
            # la variedad concreta (Vulgar/Clásico/…) se registra aparte en cognate_set.ancestor_lect.
            ("latin", ["la", "la-vul", "la-lat", "la-cla", "la-ecc", "la-med", "la-eme",
                       "la-new", "la-ren", "la-afr", "VL.", "LL."], "atestiguado"),
            ("proto-italic", ["itc-pro"], "reconstruido"),
            ("proto-ie", ["ine-pro"], "reconstruido"),
        ],
        "kaikki_files": {
            "Latin": "la", "Spanish": "es", "Italian": "it", "French": "fr", "Portuguese": "pt",
            "Catalan": "ca", "Romanian": "ro", "Occitan": "oc", "Sardinian": "sc", "Sicilian": "scn",
            "Neapolitan": "nap", "Galician": "gl", "Aromanian": "rup", "Friulian": "fur", "Ladin": "lld",
            "Walloon": "wa", "Old_French": "fro", "Old_Spanish": "osp",
        },
        "reconcile_pairs": {
            "lati1261": "la", "stan1288": "es", "ital1282": "it", "stan1290": "fr",
            "port1283": "pt", "stan1289": "ca", "roma1327": "ro", "neap1235": "nap",
        },
    },
    # ───────────────────────── ITÁLICO (rama hermana: Latín + Sabélico/Falisco bajo Proto-Itálico) ─────────────────────────
    # Sub-sistema para comparar Latín ↔ Osco/Umbro/Falisco (hermanas, no descendientes). Datos: Umbro + Proto-Itálico
    # cargables; Osco/Falisco/Picentino solo como ancestros etimológicos (sin dump Kaikki). NO se corre aún.
    "italic": {
        "members": ["la", "itc-pro", "xum", "osc", "xfa", "spx"],
        "ancestors": [
            ("proto-italic", ["itc-pro"], "reconstruido"),
            ("proto-ie", ["ine-pro"], "reconstruido"),
        ],
        "kaikki_files": {"Proto-Italic": "itc-pro", "Umbrian": "xum"},
        "all_load": ["Proto-Italic", "Umbrian"],   # antiguas/reconstruidas sin etimología → cargar toda entrada
        "reconcile_pairs": {"proto-italic": "itc-pro"},
    },
    # ───────────────────────── INDO-IRANIO (prueba multi-script: devanagari + perso-árabe) ─────────────────────────
    # Genealogía (cuidado, Alejandro): Védico/Sánscrito = indoario ATESTIGUADO (no proto); Avéstico = iranio,
    # hermana del indoario; el proto común reconstruido es Proto-Indo-Iranio (iir-pro ≈ "proto-ario").
    "indo-iranian": {
        "members": ["hi", "ur", "sa", "fa", "pa", "bn", "mr", "gu", "ne", "or", "iir-pro"],
        "ancestors": [
            ("sanskrit", ["sa"], "atestiguado"),                # sánscrito atestiguado, ancestro de las indoarias
            ("proto-indo-aryan", ["inc-pro"], "reconstruido"),
            ("proto-indo-iranian", ["iir-pro"], "reconstruido"),   # "proto-ario"
            ("proto-ie", ["ine-pro"], "reconstruido"),
        ],
        "kaikki_files": {"Hindi": "hi", "Urdu": "ur"},          # descargados; Sanskrit/Persian a futuro
        "all_load": [],
        "reconcile_pairs": {"hind1269": "hi", "urdu1245": "ur"},
    },
    # ───────────────────────── CÉLTICO (script latino; Irlandés/Galés con IPA; Bretón/Córnico/Manés escasos) ─────────────────────────
    "celtic": {
        "members": ["ga", "cy", "br", "kw", "gv", "sga", "cel-pro"],   # goidélico(ga,gv)+britónico(cy,br,kw)
        "ancestors": [
            ("old-irish", ["sga"], "atestiguado"),                     # ancestro goidélico atestiguado (sin dump)
            ("proto-celtic", ["cel-pro"], "reconstruido"),
            ("proto-ie", ["ine-pro"], "reconstruido"),
        ],
        "kaikki_files": {"Irish": "ga", "Welsh": "cy", "Breton": "br", "Cornish": "kw", "Manx": "gv"},
        "all_load": [],
        "reconcile_pairs": {"iris1253": "ga", "wels1247": "cy", "bret1244": "br", "corn1251": "kw", "manx1243": "gv"},
    },
    # ───────────────────────── GERMÁNICO (definido, NO cargado) ─────────────────────────
    "germanic": {
        # alineado a los .jsonl descargados (2026-08): sin Middle-*/Old_Saxon/Bokmål (no hay dump);
        # + Low German (nds), Feroés (fo), Scots (sco), Nynorsk (nn).
        "members": ["en", "de", "nl", "sv", "da", "nn", "is", "af", "fy", "lb", "yi",
                    "got", "ang", "goh", "non", "nds", "fo", "sco", "gem-pro"],
        "ancestors": [
            ("proto-germanic", ["gem-pro"], "reconstruido"),
            ("proto-ie", ["ine-pro"], "reconstruido"),   # niveles separados (proto-lenguas distintas)
        ],
        "kaikki_files": {
            "English": "en", "German": "de", "Dutch": "nl", "Swedish": "sv", "Danish": "da",
            "Norwegian_Nynorsk": "nn", "Icelandic": "is", "Afrikaans": "af", "West_Frisian": "fy",
            "Luxembourgish": "lb", "Yiddish": "yi", "Gothic": "got", "Old_English": "ang",
            "Old_High_German": "goh", "Old_Norse": "non", "Low_German": "nds", "Faroese": "fo",
            "Scots": "sco", "Proto-Germanic": "gem-pro",
        },
        "all_load": ["Proto-Germanic"],   # proto reconstruido, sin etimología
        "reconcile_pairs": {
            "stan1293": "en", "stan1295": "de", "dutc1256": "nl", "swed1254": "sv",
            "dani1285": "da", "icel1247": "is", "goth1244": "got",
        },
    },
    # ───────────────────────── ESLAVO (definido, NO cargado) ─────────────────────────
    "slavic": {
        # alineado a los .jsonl descargados (2026-08): sin be/mk/hr/sr/bs/cu (no hay dump).
        "members": ["ru", "pl", "cs", "sk", "uk", "bg", "sl", "sla-pro"],
        "ancestors": [
            ("proto-slavic", ["sla-pro"], "reconstruido"),
            ("proto-balto-slavic", ["bat-pro"], "reconstruido"),
            ("proto-ie", ["ine-pro"], "reconstruido"),   # niveles separados (proto-lenguas distintas)
        ],
        "kaikki_files": {
            "Russian": "ru", "Polish": "pl", "Czech": "cs", "Slovak": "sk", "Ukrainian": "uk",
            "Bulgarian": "bg", "Slovene": "sl", "Proto-Slavic": "sla-pro",
        },
        "all_load": ["Proto-Slavic"],   # proto reconstruido, sin etimología
        "reconcile_pairs": {
            "russ1263": "ru", "poli1260": "pl", "czec1258": "cs", "slov1269": "sk",
            "ukra1253": "uk", "bulg1262": "bg", "slov1268": "sl",
        },
    },
}


def active():
    """(nombre, config) de la familia activa (CI_FAMILY, default 'romance')."""
    name = os.environ.get("CI_FAMILY", "romance")
    if name not in FAMILIES:
        raise SystemExit(f"CI_FAMILY desconocida: '{name}'. Opciones: {', '.join(FAMILIES)}")
    return name, FAMILIES[name]


def _is_ancestor_code(code):
    """¿el código es una proto-lengua / ancestro reconstruido? (carga con --all: su valor es la FORMA, no su ety)"""
    return code.endswith("-pro") or code in {"cu"}  # protos + estadios antiguos sin etimología rica


def load_plan(name):
    """Plan de carga ORDENADO para una familia: (archivos_normales, archivos_ancestro[--all]).
    Ancestro/--all = declarado en `all_load` O código proto: no traen etimología (su valor es la forma)."""
    cfg = FAMILIES[name]
    all_load = set(cfg.get("all_load", []))
    normal, ancestor = [], []
    for fname, code in cfg["kaikki_files"].items():
        (ancestor if (fname in all_load or _is_ancestor_code(code)) else normal).append(fname)
    return normal, ancestor


if __name__ == "__main__":   # CLI para add_family.sh: imprime archivos/códigos a cargar
    import sys
    fam = sys.argv[1] if len(sys.argv) > 1 else "romance"
    mode = sys.argv[2] if len(sys.argv) > 2 else "normal"
    cfg = FAMILIES[fam]
    normal, ancestor = load_plan(fam)
    if mode == "protos":     # códigos de lect de los ancestros sin IPA (para esqueleto ortográfico)
        print(" ".join(cfg["kaikki_files"][f] for f in ancestor))
    else:
        print(" ".join(ancestor if mode == "ancestor" else normal))


def members():
    return active()[1]["members"]


def ancestor_tiers():
    return active()[1]["ancestors"]


def all_kaikki_files():
    """Unión de mapas de archivo→código de TODAS las familias (el loader mapea lo que encuentre)."""
    out = {}
    for f in FAMILIES.values():
        out.update(f["kaikki_files"])
    return out


def all_reconcile_pairs():
    out = {}
    for f in FAMILIES.values():
        out.update(f["reconcile_pairs"])
    return out
