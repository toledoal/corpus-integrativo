#!/usr/bin/env python3
"""Capa G2P — ELABORA IPA (grafema→fonema) para formas SIN IPA de fuente → `form.ipa_elab`.

Arquitectura (Alejandro): palabra → IPA (elaborar si falta) → esqueleto → OAS. Precedencia: IPA de la FUENTE
> IPA elaborada. Aquí se llena `ipa_elab` (no se toca `ipa_raw`); `segment_kaikki` usa coalesce(ipa_raw, ipa_elab)
→ el esqueleto sale igual de una u otra, con la procedencia registrada.

Motor: epitran (G2P por lengua/script). SOLO las lenguas con modelo fiable (probado en pre-flight). Nota: para el
esqueleto CONSONÁNTICO, incluso un G2P de abjad sin vocales (Urdu) da los consonantes correctos → código correcto.
Las lenguas sin modelo epitran (Sánscrito, Osetio, Nepalí…) se cubren por el esqueleto ORTOGRÁFICO (romanize).

Uso: .venv/bin/python ingest/elaborate_ipa.py [lect …]   (sin args = todas las del mapa)
"""
import sys
import psycopg
from config import DSN

# lect → código epitran (los que dieron IPA fiable en el pre-flight de cobertura)
G2P = {"hi": "hin-Deva", "mr": "mar-Deva", "bn": "ben-Beng", "or": "ori-Orya", "pa": "pan-Guru",
       "si": "sin-Sinh", "ur": "urd-Arab", "tg": "tgk-Cyrl", "lv": "lav-Latn", "lt": "lit-Latn"}

# rangos de scripts de FUENTE: si aparecen en la "IPA", epitran NO transliteró → salida inválida, se descarta.
def _clean_ipa(s):
    """True si la salida es IPA de verdad (sin caracteres del script fuente sin transliterar)."""
    for ch in s:
        cp = ord(ch)
        if (0x0400 <= cp <= 0x04FF or 0x0530 <= cp <= 0x05FF or 0x0600 <= cp <= 0x06FF or
                0x0900 <= cp <= 0x0DFF or 0x4E00 <= cp <= 0x9FFF):    # cirílico/hebreo/árabe/índicas/han
            return False
    return True


def main():
    import epitran
    import warnings; warnings.filterwarnings("ignore")
    want = sys.argv[1:] or list(G2P)
    conn = psycopg.connect(DSN); cur = conn.cursor()
    total = 0
    for lect in want:
        code = G2P.get(lect)
        if not code:
            print(f"  · {lect}: sin modelo G2P (usar esqueleto ortográfico)"); continue
        cur.execute("""SELECT id, orthography FROM form
                       WHERE source_id='kaikki' AND lect_id=%s AND ipa_raw IS NULL AND ipa_elab IS NULL
                         AND orthography IS NOT NULL""", (lect,))
        rows = cur.fetchall()
        if not rows:
            print(f"  · {lect}: nada por elaborar"); continue
        epi = epitran.Epitran(code)
        buf = []
        for fid, orth in rows:
            try:
                ipa = epi.transliterate(orth)
            except Exception:
                ipa = ""
            if ipa and ipa != orth and _clean_ipa(ipa):   # transliteró Y la salida es IPA limpia (no basura)
                buf.append((fid, "/" + ipa + "/"))
        if buf:
            cur.execute("CREATE TEMP TABLE _e(id TEXT PRIMARY KEY, ipa TEXT) ON COMMIT DROP")
            with cur.copy("COPY _e(id, ipa) FROM STDIN") as cp:
                for r in buf:
                    cp.write_row(r)
            cur.execute("UPDATE form f SET ipa_elab=e.ipa FROM _e e WHERE f.id=e.id")
            cur.execute("DROP TABLE _e"); conn.commit()
        print(f"  · {lect} ({code}): {len(buf):,}/{len(rows):,} elaboradas")
        total += len(buf)
    print(f"OK · IPA elaborada (G2P) = {total:,} formas")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
