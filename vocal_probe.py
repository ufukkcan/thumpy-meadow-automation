"""
VOKAL KESIF (ses uretmez): Hanami Hoshino ~AI-dol~ DiffSinger v1.0 ses bankasini indirir ve
yapisini raporlar -> out/vocal_probe_report.txt

Rapor: zip SHA256 (sabitlemek icin), dosya agaci, tum .yaml / .txt / readme icerikleri,
Ingilizce sozluk ornegi, her .onnx modelin giris/cikis adlari ve sekilleri.

DIKKAT (ToU): "Do NOT reupload the original voicebank elsewhere" -> ses bankasi ASLA
artifact olarak yuklenmez, repoya konmaz. Sadece actions/cache (disariya kapali) kullanilir.
"""
import hashlib
import re
import urllib.request
import zipfile
from pathlib import Path

PAGE = "https://www.mediafire.com/file/ks3hpb5zldabo3s/Hoshino_Hanami_%257EAIdol%257E_for_DiffSinger_v1.0.zip/file"
VB_DIR = Path("voicebank_cache")
ZIP = VB_DIR / "hanami_v1.0.zip"
OUT = Path("out")
UA = {"User-Agent": "Mozilla/5.0"}


def download() -> None:
    if ZIP.exists() and ZIP.stat().st_size > 100_000_000:
        return
    VB_DIR.mkdir(exist_ok=True)
    html = urllib.request.urlopen(urllib.request.Request(PAGE, headers=UA), timeout=60).read().decode("utf-8", "ignore")
    m = re.search(r'https?://download\d*\.mediafire\.com/[^"\'\s]+', html)
    if not m:
        raise RuntimeError("MediaFire indirme linki sayfada bulunamadi (sayfa yapisi degismis olabilir).")
    with urllib.request.urlopen(urllib.request.Request(m.group(0), headers=UA), timeout=600) as r, open(ZIP, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    download()
    rep = []
    h = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    rep.append(f"ZIP: {ZIP.stat().st_size / 1e6:.1f} MB  sha256={h}")

    root = VB_DIR / "hanami"
    if not root.exists():
        with zipfile.ZipFile(ZIP) as z:
            z.extractall(root)

    rep.append("\n== DOSYA AGACI ==")
    files = sorted(p for p in root.rglob("*") if p.is_file())
    for p in files:
        rep.append(f"{p.stat().st_size / 1e6:9.2f} MB  {p.relative_to(root)}")

    rep.append("\n== METIN DOSYALARI (yaml/txt/md/json, ilk 80 satir; buyuk sozlukler haric) ==")
    for p in files:
        if p.suffix.lower() in (".yaml", ".yml", ".txt", ".md", ".json", ".ini") and p.stat().st_size < 200_000:
            rep.append(f"\n----- {p.relative_to(root)} -----")
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            rep += lines[:80]
            if len(lines) > 80:
                rep.append(f"... ({len(lines)} satir)")

    rep.append("\n== SOZLUKLER (buyuk olanlar: ilk 40 satir) ==")
    for p in files:
        if p.suffix.lower() in (".yaml", ".yml", ".txt") and p.stat().st_size >= 200_000:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            rep.append(f"\n----- {p.relative_to(root)} ({len(lines)} satir) -----")
            rep += lines[:40]

    rep.append("\n== ONNX MODELLER ==")
    import onnxruntime as ort
    for p in files:
        if p.suffix.lower() != ".onnx":
            continue
        rep.append(f"\n----- {p.relative_to(root)} -----")
        try:
            s = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
            for i in s.get_inputs():
                rep.append(f"  IN  {i.name:24s} {i.type:20s} {i.shape}")
            for o in s.get_outputs():
                rep.append(f"  OUT {o.name:24s} {o.type:20s} {o.shape}")
            meta = s.get_modelmeta().custom_metadata_map
            if meta:
                rep.append(f"  META {meta}")
        except Exception as exc:
            rep.append(f"  ACILAMADI: {exc}")

    text = "\n".join(rep)
    (OUT / "vocal_probe_report.txt").write_text(text + "\n", encoding="utf-8")
    print(text[:20000])


if __name__ == "__main__":
    main()
