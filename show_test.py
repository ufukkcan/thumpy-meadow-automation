"""
Yeni format uctan uca test (7d, D7): Telegram'a ve YouTube'a HICBIR SEY gondermez.
1) Claude: 3 fikir -> ilk fikir -> tam senaryo (gercek API) ; ya da SHOW_JSON verilirse o senaryo
2) Tahmini sure (Telegram onay mesajindaki) vs gercek sure
3) Tam render + kontrol kareleri + 3 kucuk resim + telefon onizlemesi
4) Aciklama, yerellestirmeler, senaryo metni dosyaya
Cikti: out/ (episode.mp4, kare_*.png, thumb_*.jpg, thumb_onizleme.png, senaryo.txt, aciklama.txt, rapor.txt)
"""
import json
import os
import time
from pathlib import Path

import animal_sounds
import generate_episode as gen
from produce import estimate_minutes, produce

OUT = Path("out")


def shorts_only(ep):
    """Hizli mod (SHORTS_ONLY=1): tam bolum render edilmeden yalnizca 2 Short (ses yine tam uretilir)."""
    import show
    t0 = time.time()
    P = show.build(ep, OUT / "work")
    shorts = show.render_shorts(P, OUT / "work", n=2, frames_dir=str(OUT))
    rep = [f"Shorts modu: {(time.time() - t0) / 60:.1f} dk"]
    for sh in shorts:
        Path(sh["path"]).replace(OUT / Path(sh["path"]).name)
        meta = gen.short_meta(ep, sh["find"], os.environ.get("FULL_VIDEO_ID"))
        rep += [f"- {Path(sh['path']).name}: {sh['dur']:.1f} sn", f"  {meta['title']}", f"  {meta['description']}"]
    (OUT / "rapor.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))


def main():
    OUT.mkdir(exist_ok=True)
    if os.environ.get("SHORTS_ONLY") == "1":
        return shorts_only(json.loads(Path(os.environ["SHOW_JSON"]).read_text(encoding="utf-8")))
    rep = []
    if os.environ.get("SHOW_JSON") and Path(os.environ["SHOW_JSON"]).exists():
        ep = json.loads(Path(os.environ["SHOW_JSON"]).read_text(encoding="utf-8"))
        rep.append(f"Senaryo dosyadan: {os.environ['SHOW_JSON']}")
    else:
        t0 = time.time()
        ideas = gen.generate_ideas()
        rep.append(f"Fikirler ({time.time() - t0:.0f} sn):")
        rep += [f"  - {i.get('working_title')} [{i.get('frame')}] {i.get('animals')}" for i in ideas]
        t0 = time.time()
        ep = gen.generate_script(ideas[0])
        rep.append(f"Senaryo ({time.time() - t0:.0f} sn); sarki sorunlari: {ep.get('song_issues')}")
    (OUT / "senaryo.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")
    est = estimate_minutes(ep)
    (OUT / "senaryo.txt").write_text(gen.script_as_text(ep, est), encoding="utf-8")
    rep.append(f"Tahmini sure: {est:.2f} dk")
    rep += animal_sounds.report()                   # 11 hayvanin hepsi: bir kayit bozuksa render'dan once ciksin
    print("\n".join(rep), flush=True)

    t0 = time.time()
    res = produce(ep, OUT / "work", frames_dir=str(OUT))
    rep.append(f"Uretim: {(time.time() - t0) / 60:.1f} dk; gercek sure {res['total'] / 60:.2f} dk "
               f"(tahmin {est:.2f})")
    for p in res["thumbnails"] + [res["thumb_preview"]]:
        Path(p).replace(OUT / Path(p).name)
    Path(res["video"]).replace(OUT / "episode.mp4")
    desc = gen.build_description(ep, res["chapters"])
    locs = gen.build_localizations(ep, res["chapters"])
    (OUT / "aciklama.txt").write_text(
        f"BASLIK: {ep['title']}\n\n{desc}\n\nETIKETLER: {', '.join(ep['tags'])}\n\n"
        + "\n\n".join(f"[{k}] {v['title']}\n{v['description']}" for k, v in locs.items()), encoding="utf-8")
    rep.append("Bolumler: " + " | ".join(f"{int(t // 60)}:{int(t % 60):02d} {n}" for t, n in res["chapters"]))
    (OUT / "rapor.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep[-2:]))


if __name__ == "__main__":
    main()
