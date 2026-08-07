#!/usr/bin/env python3
"""Raspa Pokorny (StarLing/Starostin) → data/lexicon/pokorny/pokorny.jsonl. 2.222 raíces PIE con reflejos por rama.
Educado (delay), resumible (salta las ya guardadas). Uso: .venv/bin/python ingest/scrape_pokorny.py [N_max]"""
import json, os, re, sys, time, urllib.request
OUT="/Users/alejandrotoledo/Documents/development/largelanguage/endolanguage/data/lexicon/pokorny/pokorny.jsonl"
URL=("https://starlingdb.org/cgi-bin/etymology.cgi?single=1&basename=/data/ie/pokorny&text_number={n}&root=config")
# campos que nos interesan (Pokorny + capa IE de Starostin)
LABELS=["Number","Root","English meaning","German meaning","Proto-IE","Meaning","Old Indian","Old Greek",
        "Latin","Other Italic","Germanic","Baltic","Slavic","Celtic","Albanian","Tocharian","Armenian",
        "Hittite","Anatolian","Avestan","Iranian","Material","Pages"]
_lab=re.compile(r"(" + "|".join(re.escape(l) for l in LABELS) + r"):")

def parse(txt):
    # recorta a la sección IE + Pokorny (evita Nostratic/Altaic/etc. que vienen después)
    txt=re.sub(r"<[^>]*>"," ",txt); txt=re.sub(r"&nbsp;"," ",txt); txt=re.sub(r"&lt;","<",txt); txt=re.sub(r"&gt;",">",txt)
    cut=txt.find("Nostratic etymology :")
    if cut>0: txt=txt[:cut]
    d={}; ms=list(_lab.finditer(txt))
    for i,m in enumerate(ms):
        lab=m.group(1); end=ms[i+1].start() if i+1<len(ms) else len(txt)
        val=txt[m.end():end].strip(" :\t")
        val=re.split(r"\s+(?:Nostratic|Indo-European|Baltic|Germanic|Vasmer|Altaic) etymology", val)[0].strip()
        if lab not in d and val: d[lab]=val[:800]
    return d

def main():
    N=int(sys.argv[1]) if len(sys.argv)>1 else 2230
    done=set()
    if os.path.exists(OUT):
        for line in open(OUT): 
            try: done.add(json.loads(line)["n"])
            except: pass
    f=open(OUT,"a",encoding="utf-8"); got=0
    for n in range(1,N+1):
        if n in done: continue
        try:
            html=urllib.request.urlopen(URL.format(n=n),timeout=30).read().decode("utf-8","replace")
        except Exception as e:
            print(f"  {n}: err {str(e)[:30]}"); continue
        d=parse(html); d["n"]=n
        if d.get("Root") or d.get("Proto-IE"):
            f.write(json.dumps(d,ensure_ascii=False)+"\n"); f.flush(); got+=1
        if n%100==0: print(f"  … {n} (guardadas {got})",flush=True)
        time.sleep(0.35)
    print(f"OK · nuevas={got}")


if __name__ == "__main__":
    main()
