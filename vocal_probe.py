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
import subprocess
import sys
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

    _flush(rep)   # onnx bolumunde bir sey cokse bile buraya kadarki bilgi kaybolmasin

    rep.append("\n== ONNX MODELLER (onnx paketiyle dosyadan okunur -- calistirma motoru kullanilmaz) ==")
    import onnx
    onnx_files = [p for p in files if p.suffix.lower() == ".onnx"]
    for p in onnx_files:
        rep.append(f"\n----- {p.relative_to(root)} -----")
        try:
            m = onnx.load(str(p), load_external_data=False)
            opsets = ", ".join(f"{o.domain or 'ai.onnx'}:{o.version}" for o in m.opset_import)
            rep.append(f"  ir={m.ir_version} opset=[{opsets}] producer={m.producer_name} {m.producer_version}")
            inits = {i.name for i in m.graph.initializer}
            for io, lst in (("IN ", m.graph.input), ("OUT", m.graph.output)):
                for v in lst:
                    if v.name in inits:
                        continue
                    t = v.type.tensor_type
                    dims = [d.dim_param or d.dim_value for d in t.shape.dim]
                    rep.append(f"  {io} {v.name:24s} {onnx.TensorProto.DataType.Name(t.elem_type):8s} {dims}")
            if m.metadata_props:
                rep.append(f"  META { {x.key: x.value for x in m.metadata_props} }")
        except Exception as exc:
            rep.append(f"  OKUNAMADI: {exc}")
        _flush(rep)

    rep.append("\n== onnxruntime yukleme testi (her model ayri surecte; cokme diger modelleri etkilemez) ==")
    for p in onnx_files:
        for level in ("ORT_ENABLE_ALL", "ORT_DISABLE_ALL"):
            code = ("import onnxruntime as ort; o = ort.SessionOptions(); "
                    f"o.graph_optimization_level = ort.GraphOptimizationLevel.{level}; "
                    f"ort.InferenceSession({str(p)!r}, o, providers=['CPUExecutionProvider'])")
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
            msg = "OK" if r.returncode == 0 else f"HATA (kod {r.returncode}): {r.stderr.strip().splitlines()[-1][:160] if r.stderr.strip() else ''}"
            rep.append(f"  {str(p.relative_to(root)):60s} {level:16s} {msg}")
        _flush(rep)
    print("\n".join(rep)[:30000])


def _flush(rep: list[str]) -> None:
    (OUT / "vocal_probe_report.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
