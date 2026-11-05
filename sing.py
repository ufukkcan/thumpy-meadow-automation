"""
Hanami Hoshino ~AI-dol~ (DiffSinger ses bankasi, Lotte V) ile sarki soyletme -- sadece CPU.

LISANS (docs/kararlar.md K-18):
  - akustik model + sozluk: ticari kullanim serbest, KAYNAK GOSTERME SART ("Lotte V")
  - bankanin kendi vocoder'i (AI-dolGAN): CC BY-NC-SA -> KULLANILMAZ
  - vocoder: NVIDIA BigVGAN-v2 44 kHz (MIT), sabit surum
  - ToU: ses bankasi ASLA repoya / artifact'a konmaz (yalnizca actions/cache)

Akis:
  soz -> fonem (bankanin dsdict-en.yaml sozlugu) -> heceler notalara
  -> fonem sureleri nota izgarasina: UNLU NOTANIN BASINDA baslar, bastaki unsuzler
     notadan ONCE (kulak vurusu unlude duyar)
  -> f0 egrisi: notalar + yumusak gecis (portamento) + uzun notalarda vibrato
  -> acoustic.onnx -> mel (40-16000 Hz bantlari) -> BigVGAN bantlarina (0-22050 Hz)
  -> BigVGAN -> ses
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

import songs

SR = 44100
HOP = 512
VB_DIR = Path(__file__).resolve().parent / "voicebank_cache"
VB_ZIP = VB_DIR / "hanami_v1.0.zip"
VB_SHA256 = "91d9302cb220ba2c790a01973b0cc6ab1d84df3581582a1a4b1fb9acc4f65277"
VB_PAGE = "https://www.mediafire.com/file/ks3hpb5zldabo3s/Hoshino_Hanami_%257EAIdol%257E_for_DiffSinger_v1.0.zip/file"
VB_NAME = "Hoshino Hanami ~AIdol~ for DiffSinger v1.0"

BIGVGAN_REPO = "nvidia/bigvgan_v2_44khz_128band_512x"
BIGVGAN_REV = "95a9d1dcb12906c03edd938d77b9333d6ded7dfb"

# Ingilizce telaffuz: CMU Pronouncing Dictionary (BSD lisansi), sabit surum. OpenUtau'nun
# Ingilizce fonemleyicisi de bunu kullanir; bankanin dsdict-en.yaml'i sadece ek girisler icerir.
CMUDICT_URL = "https://raw.githubusercontent.com/cmusphinx/cmudict/74790861f652b15e4ac49015a90074ad62a27690/cmudict.dict"

CREDIT ="Singing voice: Hoshino Hanami ~AI-dol~ by Lotte V (lottev.moe); vocoder: NVIDIA BigVGAN (MIT)"

# unsuz sureleri (sn), dsdict 'type' alanina gore
CONS_DUR = {"stop": 0.055, "affricate": 0.08, "fricative": 0.085, "nasal": 0.065, "liquid": 0.055,
            "semivowel": 0.05, "aspirate": 0.05, "glottal": 0.04}
PORTAMENTO = 0.07          # nota gecisi (sn)
VIB_RATE, VIB_DEPTH = 5.5, 0.30   # Hz, yarim ton
VIB_DELAY, VIB_MIN_NOTE = 0.25, 0.45


# ---------------- ses bankasi ----------------
def ensure_voicebank() -> Path:
    root = VB_DIR / "hanami" / VB_NAME
    if root.exists():
        return root
    VB_DIR.mkdir(exist_ok=True)
    if not (VB_ZIP.exists() and VB_ZIP.stat().st_size > 100_000_000):
        ua = {"User-Agent": "Mozilla/5.0"}
        html = urllib.request.urlopen(urllib.request.Request(VB_PAGE, headers=ua), timeout=60).read().decode("utf-8", "ignore")
        m = re.search(r'https?://download\d*\.mediafire\.com/[^"\'\s]+', html)
        if not m:
            raise RuntimeError("MediaFire indirme linki bulunamadi.")
        with urllib.request.urlopen(urllib.request.Request(m.group(0), headers=ua), timeout=600) as r, open(VB_ZIP, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    h = hashlib.sha256(VB_ZIP.read_bytes()).hexdigest()
    if h != VB_SHA256:
        raise RuntimeError(f"Ses bankasi zip'i beklenen dosya degil (sha256 {h}).")
    with zipfile.ZipFile(VB_ZIP) as z:
        z.extractall(VB_DIR / "hanami")
    return root


def _load_cmudict() -> dict[str, list[str]]:
    """'word  AH0 B AW1 T' -> {'word': ['ah','b','aw','t']} (vurgu rakamlari atilir, ilk telaffuz)."""
    path = VB_DIR / "cmudict.dict"
    if not path.exists():
        VB_DIR.mkdir(exist_ok=True)
        with urllib.request.urlopen(CMUDICT_URL, timeout=60) as r:
            path.write_bytes(r.read())
    out = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *ph = line.split()
        if "(" in word or word in out:      # 'word(2)' gibi alternatif telaffuzlar atlanir
            continue
        out[word] = [re.sub(r"\d", "", p).lower() for p in ph]
    if len(out) < 100_000:
        raise RuntimeError(f"CMU sozlugu eksik yuklendi ({len(out)} kelime).")
    return out


_CMU: dict | None = None
ARPA_VOWELS = {"aa", "ae", "ah", "ao", "aw", "ay", "eh", "er", "ey", "ih", "iy", "ow", "oy", "uh", "uw"}


def cmu() -> dict[str, list[str]]:
    """CMU sozlugu (bir kez yuklenir). Ses modeli gerektirmez -> senaryo dogrulamasinda da kullanilir."""
    global _CMU
    if _CMU is None:
        _CMU = _load_cmudict()
    return _CMU


def _norm(word: str) -> str:
    return re.sub(r"[^a-z']", "", word.lower().replace("’", "'"))


def cmu_phonemes(word: str) -> list[str] | None:
    w = _norm(word)
    for cand in (w, w.strip("'")):
        if cand in cmu():
            return cmu()[cand]
    return None


def syllable_count(word: str) -> int | None:
    """Soylenen hece sayisi = CMU telaffuzundaki unlu sayisi (sozlukte yoksa None)."""
    ph = cmu_phonemes(word)
    return sum(p in ARPA_VOWELS for p in ph) if ph else None


def _yaml(path: Path):
    import yaml
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(path.read_text(encoding="utf-8"), Loader=loader)


class Singer:
    def __init__(self, speaker: str = "Root", steps: int = 20, depth: float = 0.6):
        import onnxruntime as ort
        root = ensure_voicebank()
        cfg = _yaml(root / "dsconfig.yaml")
        for k, v in (("sample_rate", SR), ("hop_size", HOP), ("num_mel_bins", 128), ("mel_base", "e"),
                     ("mel_scale", "slaney")):
            if cfg.get(k) != v:
                raise RuntimeError(f"dsconfig.yaml beklenmeyen {k}={cfg.get(k)}")
        self.fmin, self.fmax = float(cfg["mel_fmin"]), float(cfg["mel_fmax"])
        self.steps, self.depth = int(steps), float(min(depth, cfg.get("max_depth", depth)))
        self.phonemes = [l.strip() for l in (root / "dsmain/phonemes.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
        self.tok = {p: i for i, p in enumerate(self.phonemes)}

        d = _yaml(root / "dsdur/dsdict-en.yaml")
        self.types = {str(s["symbol"]): str(s["type"]) for s in d["symbols"]}
        self.lex = {str(e["grapheme"]).lower(): [str(p) for p in e["phonemes"]] for e in d.get("entries", [])}
        self.cmu = cmu()

        # ses modlari: Root (normal), Fragrance (guclu), Nectar (yumusak)
        self.embs = {}
        for p in sorted((root / "dsmain/embeds/acoustic").glob("*.emb")):
            e = np.fromfile(p, dtype=np.float32)
            if e.size != int(cfg["hidden_size"]):
                raise RuntimeError(f"{p.name} boyutu {e.size}, beklenen {cfg['hidden_size']}")
            self.embs[p.stem] = e
        self.speaker = speaker
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL   # E10: aciksa cokuyor
        self.sess = ort.InferenceSession(str(root / cfg["acoustic"]), so, providers=["CPUExecutionProvider"])

        # otomatik perde (Hanami'nin kendi sarki soyleyisinden ogrenilmis): dspitch/
        pcfg = _yaml(root / "dspitch/dsconfig.yaml")
        self.pitch_ling = ort.InferenceSession(str(root / "dspitch" / pcfg["linguistic"]), so, providers=["CPUExecutionProvider"])
        self.pitch_sess = ort.InferenceSession(str(root / "dspitch" / pcfg["pitch"]), so, providers=["CPUExecutionProvider"])
        self.pitch_embs = {Path(s).name: np.fromfile(root / "dspitch" / f"{s}.emb", dtype=np.float32)
                           for s in pcfg["speakers"]}
        self.timing = {}

    # ---- sozluk ----
    def lookup(self, word: str) -> list[str]:
        ph = cmu_phonemes(word)           # once CMU sozlugu (standart Ingilizce telaffuz)
        if ph:
            return ph
        w = _norm(word)
        for cand in (w, w.strip("'"), w.replace("'", "")):
            if cand in self.lex:          # yoksa bankanin ek girisleri (isimler, ozel kelimeler)
                return self.lex[cand]
        raise KeyError(word)

    def missing_words(self, lyrics: list[str]) -> list[str]:
        out = []
        for line in lyrics:
            for w in line.split():
                try:
                    self.lookup(w)
                except KeyError:
                    out.append(w)
        return out

    def syllables(self, word: str) -> list[tuple[list[str], str, list[str]]]:
        """Kelime -> [(bas_unsuzler, unlu, son_unsuzler)]. Iki unlu arasindaki unsuzlerin
        yarisi (asagi yuvarlanir) onceki heceye, kalani sonrakine (ba-na-na, ap-ple)."""
        ph = self.lookup(word)
        for p in ph:
            if p not in self.tok:
                raise RuntimeError(f"'{word}' fonemi '{p}' modelde yok")
        vid = [i for i, p in enumerate(ph) if self.types.get(p) == "vowel"]
        if not vid:
            raise RuntimeError(f"'{word}' icin unlu bulunamadi: {ph}")
        bounds = [0] + [a + 1 + (b - a - 1) // 2 for a, b in zip(vid[:-1], vid[1:])] + [len(ph)]
        out = []
        for k, v in enumerate(vid):
            seg = ph[bounds[k]:bounds[k + 1]]
            j = v - bounds[k]
            out.append((seg[:j], seg[j], seg[j + 1:]))
        return out

    def _cdur(self, p: str) -> float:
        return CONS_DUR.get(self.types.get(p, ""), 0.06)

    # ---- notalar -> fonem zaman cizelgesi ----
    def score(self, lyrics: list[str], lines: list, line_starts: list[float], beat: float):
        """Donus: slots = [{on, v, co, t0, t1, notes:[(t0,t1,midi)], phrase_end}]"""
        slots = []
        for text, notes, ls in zip(lyrics, lines, line_starts):
            times, t = [], ls
            for midi, b in notes:
                times.append((t, t + b * beat, float(midi)))
                t += b * beat
            ni = 0
            for word, wnotes in songs.map_words_to_notes(text, notes, counter=lambda w: len(self.syllables(w))):
                n = len(wnotes)
                mine = times[ni:ni + n]
                ni += n
                syl = [s for tok in word.split() for s in self.syllables(tok)]
                k = len(syl)
                if k <= n:   # fazla nota: son hece notalar boyunca uzar (melizma)
                    groups = [[mine[i]] for i in range(k - 1)] + [mine[k - 1:]]
                else:        # fazla hece: son nota esit parcalara bolunur
                    a, b, m = mine[-1]
                    parts = k - n + 1
                    sub = [(a + (b - a) * i / parts, a + (b - a) * (i + 1) / parts, m) for i in range(parts)]
                    groups = [[x] for x in mine[:-1]] + [[x] for x in sub]
                for (on, v, co), g in zip(syl, groups):
                    slots.append({"on": on, "v": v, "co": co, "t0": g[0][0], "t1": g[-1][1], "notes": g,
                                  "phrase_end": False})
            if slots:
                slots[-1]["phrase_end"] = True
        return slots

    def phones(self, slots: list[dict]) -> tuple[list[tuple[str, float, float]], list[float]]:
        """Hece yuvalari -> ([(fonem, bas, son)], her hecenin ilk fonem baslangici).
        Bosluklar SP ile doldurulur."""
        on_len = []
        for i, s in enumerate(slots):
            want = sum(self._cdur(p) for p in s["on"])
            prev_len = (slots[i - 1]["t1"] - slots[i - 1]["t0"]) if i else 0.3
            on_len.append(min(want, 0.45 * prev_len, 0.25))
        out = []
        for i, s in enumerate(slots):
            t0, t1 = s["t0"], s["t1"]
            if s["on"]:   # bas unsuzler notadan once, orantili
                total = sum(self._cdur(p) for p in s["on"])
                t = t0 - on_len[i]
                for p in s["on"]:
                    d = on_len[i] * self._cdur(p) / total
                    out.append((p, t, t + d))
                    t += d
            end = t1
            if s["phrase_end"]:
                end = t1 - max(0.10, 0.15 * (t1 - t0))      # satir sonu: nefes payi
            elif i + 1 < len(slots) and abs(slots[i + 1]["t0"] - t1) < 1e-6:
                end = t1 - on_len[i + 1]                    # sonraki hecenin unsuzlerine yer ac
            co_want = sum(self._cdur(p) for p in s["co"])
            co_len = min(co_want, 0.4 * max(end - t0, 0.0))
            v_end = end - co_len
            out.append((s["v"], t0, max(v_end, t0 + 0.03)))
            t = v_end
            for p in s["co"]:
                d = co_len * self._cdur(p) / co_want if co_want else 0
                out.append((p, t, t + d))
                t += d
        # siralama + bosluklar: satir aralarinda NEFES (AP), basta sessizlik + nefes
        filled, cur = [], 0.0
        for p, a, b in out:
            a = max(a, cur)
            if b <= a:
                continue
            gap = a - cur
            if gap > 1e-4:
                if not filled and gap > 0.5:
                    filled += [("SP", cur, a - 0.3), ("AP", a - 0.3, a)]
                elif filled and gap >= 0.08:
                    filled.append(("AP", cur, a))
                else:
                    filled.append(("SP", cur, a))
            filled.append((p, a, b))
            cur = b
        filled.append(("SP", cur, cur + 0.4))
        on_starts = [s["t0"] - (on_len[i] if s["on"] else 0.0) for i, s in enumerate(slots)]
        return filled, on_starts

    def f0_curve(self, slots: list[dict], n_frames: int, on_starts: list[float]) -> np.ndarray:
        """Kare basina f0 (Hz): notalar + portamento + vibrato."""
        tc = (np.arange(n_frames) + 0.5) * HOP / SR
        bp_t, bp_m = [], []
        for s, st in zip(slots, on_starts):
            for j, (a, b, m) in enumerate(s["notes"]):
                bp_t.append(st if j == 0 else a)   # hecenin ilk notasi unsuzle birlikte baslar
                bp_m.append(m)
        idx = np.clip(np.searchsorted(bp_t, tc, side="right") - 1, 0, len(bp_m) - 1)
        midi = np.array(bp_m)[idx]
        w = max(3, int(PORTAMENTO * SR / HOP))
        win = np.hanning(w * 2 + 1)
        win /= win.sum()
        pad = np.pad(midi, (w, w), mode="edge")
        midi = np.convolve(pad, win, mode="valid")
        for s in slots:
            for a, b, m in s["notes"]:
                if b - a < VIB_MIN_NOTE:
                    continue
                sel = (tc >= a + VIB_DELAY) & (tc < b - 0.05)
                tt = tc[sel] - (a + VIB_DELAY)
                ramp = np.clip(tt / 0.25, 0, 1)
                midi[sel] += VIB_DEPTH * ramp * np.sin(2 * np.pi * VIB_RATE * tt)
        return 440.0 * 2 ** ((midi - 69) / 12)

    def auto_pitch(self, tokens: np.ndarray, durs: np.ndarray, slots: list[dict], speaker: str,
                   expr: float = 1.0, steps: int = 10) -> np.ndarray:
        """pitch.onnx ile dogal perde egrisi (MIDI, kare basina). OpenUtau DiffSingerPitch.cs ile
        ayni besleme: baslangic perdesi 60, retake hepsi True, expr 1.0, sus notalari komsu
        notanin perdesiyle doldurulur."""
        n = int(durs.sum())
        enc = self.pitch_ling.run(["encoder_out"], {"tokens": tokens, "ph_dur": durs})[0]
        notes = sorted((a, b, m) for s in slots for a, b, m in s["notes"])
        dur_s, midi, rest = [notes[0][0]], [notes[0][2]], [True]          # bas sessizlik
        prev_end = notes[0][0]
        for a, b, m in notes:
            if a - prev_end > 1e-4:
                dur_s.append(a - prev_end); midi.append(m); rest.append(True)
            dur_s.append(b - a); midi.append(m); rest.append(False)
            prev_end = b
        dur_s.append(0.0); midi.append(notes[-1][2]); rest.append(True)  # son sessizlik (kalan kareler)
        # sus gruplari: basta -> sonraki, sonda -> onceki, ortada -> yarisi once yarisi sonra
        i = 0
        while i < len(rest):
            if not rest[i]:
                i += 1
                continue
            j = i
            while j < len(rest) and rest[j]:
                j += 1
            if i == 0 and j < len(rest):
                midi[i:j] = [midi[j]] * (j - i)
            elif j == len(rest):
                midi[i:j] = [midi[i - 1]] * (j - i)
            else:
                mid = (i + j + 1) // 2
                midi[i:mid] = [midi[i - 1]] * (mid - i)
                midi[mid:j] = [midi[j]] * (j - mid)
            i = j
        edges = np.round(np.cumsum([0.0] + dur_s) * SR / HOP).astype(int)
        nd = np.maximum(np.diff(edges), 0)
        nd[-1] = max(0, n - int(nd[:-1].sum()))                           # FitDurationSum
        if nd.sum() != n:
            raise RuntimeError(f"nota kareleri {nd.sum()} != fonem kareleri {n}")
        feeds = {
            "encoder_out": enc, "ph_dur": durs,
            "note_midi": np.array([midi], np.float32), "note_rest": np.array([rest], bool),
            "note_dur": np.array([nd], np.int64),
            "pitch": np.full((1, n), 60.0, np.float32), "expr": np.full((1, n), expr, np.float32),
            "retake": np.ones((1, n), bool),
            "spk_embed": np.tile(self.pitch_embs[speaker], (1, n, 1)).astype(np.float32),
            "steps": np.array(steps, np.int64),
        }
        t = time.time()
        out = self.pitch_sess.run(["pitch_pred"], feeds)[0][0]
        self.timing["pitch_s"] = time.time() - t
        return out

    def render_mel(self, lyrics, lines, line_starts, beat, speaker: str | None = None,
                   natural_pitch: bool = True):
        """Donus: (mel [frames,128] ln, f0 [frames], ph listesi, slots). Kare 0 = zaman 0.
        natural_pitch: perde Hanami'nin perde modelinden (True) ya da notalardan cizilir (False)."""
        speaker = speaker or self.speaker
        emb = self.embs[speaker]
        slots = self.score(lyrics, lines, line_starts, beat)
        ph, on_starts = self.phones(slots)
        bounds = [int(round(a * SR / HOP)) for _, a, _ in ph] + [int(round(ph[-1][2] * SR / HOP))]
        for i in range(1, len(bounds)):
            bounds[i] = max(bounds[i], bounds[i - 1] + 2)   # her fonem en az 2 kare (~23 ms): tik sesi olmasin
        tokens = np.array([[self.tok[p] for p, _, _ in ph]], dtype=np.int64)
        durs = np.array([np.diff(bounds)], dtype=np.int64)
        lead = bounds[0]                          # ilk fonemden onceki kareler (SP ile)
        if lead > 0:
            tokens = np.concatenate([[[self.tok["SP"]]], tokens], axis=1)
            durs = np.concatenate([[[lead]], durs], axis=1)
        n = int(durs.sum())
        if natural_pitch:
            midi = self.auto_pitch(tokens, durs, slots, speaker)
            f0 = (440.0 * 2 ** ((midi - 69) / 12)).astype(np.float32)
        else:
            f0 = self.f0_curve(slots, n, on_starts).astype(np.float32)
        feeds = {
            "tokens": tokens, "durations": durs, "f0": f0[None, :],
            "gender": np.zeros((1, n), np.float32), "velocity": np.ones((1, n), np.float32),
            "spk_embed": np.tile(emb, (1, n, 1)).astype(np.float32),
            "depth": np.array(self.depth, np.float32), "steps": np.array(self.steps, np.int64),
        }
        t = time.time()
        mel = self.sess.run(["mel"], feeds)[0][0]
        self.timing["acoustic_s"] = time.time() - t
        return mel, f0, ph, slots


# ---------------- vocoder: BigVGAN-v2 (MIT) ----------------
class Vocoder:
    def __init__(self):
        import torch
        from huggingface_hub import snapshot_download
        d = snapshot_download(BIGVGAN_REPO, revision=BIGVGAN_REV,
                              allow_patterns=["*.py", "alias_free_activation/torch/*", "config.json",
                                              "bigvgan_generator.pt", "LICENSE"])
        sys.path.insert(0, d)
        from bigvgan import BigVGAN
        from env import AttrDict
        h = AttrDict(json.loads(Path(d, "config.json").read_text()))
        self.h = h
        model = BigVGAN(h, use_cuda_kernel=False)
        state = torch.load(Path(d, "bigvgan_generator.pt"), map_location="cpu", weights_only=False)
        model.load_state_dict(state["generator"])
        model.remove_weight_norm()
        self.model = model.eval()
        torch.set_num_threads(os.cpu_count() or 4)
        import librosa
        self.c_bv = librosa.mel_frequencies(int(h.num_mels) + 2, fmin=float(h.fmin), fmax=float(h.fmax or SR / 2))[1:-1]
        self.timing = {}

    def ds_to_bigvgan(self, mel: np.ndarray, fmin: float, fmax: float) -> np.ndarray:
        """DiffSinger mel (40-16000 Hz) -> BigVGAN mel (0-22050 Hz).
        Iki filtre bankasi da slaney (alan normalize) -> bant degeri ~ bant merkezindeki ortalama
        genlik; bu yuzden ln-degerler merkez frekanslar arasinda (mel olceginde) enterpole edilir.
        16 kHz ustu: son degerden sessizlige (ln 1e-5) dogru dogrusal inis.
        (Deneme 1'deki 'taban genisletme' kaldirildi: -4 altindaki tum harmonikleri eziyordu -- E13.)"""
        import librosa
        c_ds = librosa.mel_frequencies(mel.shape[1] + 2, fmin=fmin, fmax=fmax)[1:-1]
        x_ds, x_bv = librosa.hz_to_mel(c_ds), librosa.hz_to_mel(self.c_bv)
        floor = np.log(1e-5)
        out = np.empty((mel.shape[0], len(x_bv)), np.float32)
        hi = x_bv > x_ds[-1]
        for i, fr in enumerate(mel):
            v = np.interp(x_bv, x_ds, fr)
            if hi.any():
                frac = (x_bv[hi] - x_ds[-1]) / (x_bv[-1] - x_ds[-1])
                v[hi] = fr[-1] + (floor - fr[-1]) * frac
            out[i] = v
        return np.maximum(out, floor)

    def __call__(self, mel_bv: np.ndarray) -> np.ndarray:
        import torch
        t = time.time()
        with torch.inference_mode():
            y = self.model(torch.from_numpy(mel_bv.T[None]).float())[0, 0].numpy()
        self.timing["vocoder_s"] = time.time() - t
        return y.astype(np.float64)


def ds_mel(y: np.ndarray, fmin: float, fmax: float) -> np.ndarray:
    """DiffSinger ile ayni tanimla mel (olcum icin): |STFT| -> slaney mel -> ln(max(x,1e-5))."""
    import librosa
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP, win_length=2048, center=True))
    M = librosa.filters.mel(sr=SR, n_fft=2048, n_mels=128, fmin=fmin, fmax=fmax)
    return np.log(np.maximum(M @ S, 1e-5)).T
