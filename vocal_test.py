"""
VOKAL TESTI (deneme 3/3) -- hicbir yere yukleme yapmaz.
Deneme 1: ritim ve perde dogru, ses kalitesi kotu; vocoder uyumu 2.1-2.4 (kok neden: mel
'taban genisletme' harmonikleri eziyordu). Deneme 2: genisletme kaldirildi -> uyum 0.31 (= kopya
sentez tavani); kullanici: "ritim cok guzel, biraz robotik, ara sira kucuk cizirtilar".
Deneme 3: Hanami'nin kendi perde modeli (dogal perde), satir aralarinda nefes (AP),
fonem en az 2 kare, tik/cizirti dedektoru.

Uretir:  out/vocal_test.mp3         Twinkle (Root = normal ses) + London Bridge (Nectar = yumusak ses),
                                     muzikle birlikte
         out/vocal_test_dry.mp3     ayni vokal, muziksiz (sesin kendisini degerlendirmek icin)
         out/vocal_test_report.txt  olcumler
Olcer:   1) eksik kelime (sozlukte olmayan)
         2) perde dogrulugu: her notanin ortasinda olculen perde - hedef (cent)
         3) ritim (tahmini): unlu baslarinin nota zamanindan sapmasi (80-1000 Hz bant enerjisi)
         4) vocoder uyumu: uretilen sesten yeniden hesaplanan mel ile modelin mel'i arasindaki fark
         5) sure: akustik model + vocoder suresi (CPU)
         6) ses yuksekligi (LUFS, gercek tepe)
"""
from pathlib import Path

import numpy as np

import kidsong
import music_test
import samples
import sing
import songs

OUT = Path("out")
LYRICS = {   # ozgun sozler (sing_test.py'den); hece sayilari melodiye uyar
    "twinkle": ["Apple, banana, so sweet", "Red and yellow, what a treat",
                "Grapes are purple, pears are green", "Yummy fruits, the best I've seen",
                "Apple, banana, so sweet", "Red and yellow, what a treat"],
    "london": ["Let us count the apples now", "one, two, three, one, two, three",
               "Let us count the apples now", "one, two, three, four"],
}
SONGS = [("twinkle", "Root"), ("london", "Nectar")]


def _band(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / samples.SR)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, len(x))


def clicks(x: np.ndarray, thr_db: float = 15.0) -> list[tuple[float, float]]:
    """Tik/cizirti dedektoru: 5 kHz ustu enerjide, 60 ms'lik yerel ortancadan thr_db yukari firlayan
    ve 6 ms icinde 10 dB'den fazla geri dusen KISA olaylar ('s', 'sh' gibi uzun surtunmeler sayilmaz).
    Donus: [(zaman_sn, siddet_dB)]"""
    from numpy.lib.stride_tricks import sliding_window_view
    hp = _band(x, 5000, 20000)
    w = int(0.002 * samples.SR)
    n = len(hp) // w
    e = 10 * np.log10(np.mean(hp[: n * w].reshape(n, w) ** 2, axis=1) + 1e-12)
    med = np.median(sliding_window_view(np.pad(e, (15, 15), mode="edge"), 31), axis=1)
    cand = np.where((e - med > thr_db) & (e > e.max() - 45))[0]
    ev = []
    for c in cand:
        if ev and c - ev[-1][1] <= 2:
            ev[-1][1] = c
        else:
            ev.append([c, c])
    out = []
    for a, b in ev:
        peak = e[a:b + 1].max()
        if b - a <= 2 and b + 3 < n and e[b + 3] < peak - 10:
            out.append((a * w / samples.SR, float(peak - med[a])))
    return out


def pitch_errors(y: np.ndarray, slots: list[dict]) -> list[float]:
    errs = []
    for s in slots:
        for a, b, m in s["notes"]:
            if b - a < 0.2:
                continue
            seg = y[int((a + 0.35 * (b - a)) * samples.SR): int((a + 0.85 * (b - a)) * samples.SR)]
            f0 = samples.detect_f0(seg, fmin=80.0, fmax=1100.0)
            if f0:
                errs.append(1200 * np.log2(f0 / (440.0 * 2 ** ((m - 69) / 12))))
    return errs


def mel_fit(y: np.ndarray, mel: np.ndarray, fmin: float, fmax: float) -> float:
    """Sesli karelerde ortalama |ln fark| (en iyi +-2 kare kayma ile)."""
    m2 = sing.ds_mel(y, fmin, fmax)
    voiced = mel.max(axis=1) > -3.0
    best = 9.9
    for lag in range(-2, 3):
        a = mel[max(0, -lag): len(mel) - max(0, lag)]
        b = m2[max(0, lag): max(0, lag) + len(a)]
        v = voiced[max(0, -lag): max(0, -lag) + len(b)]
        n = min(len(a), len(b), len(v))
        if n and v[:n].any():
            best = min(best, float(np.mean(np.abs(a[:n][v[:n]] - b[:n][v[:n]]))))
    return best


def mix(music: np.ndarray, vocal: np.ndarray) -> np.ndarray:
    """Vokal: hafif yanki, muzigin ~4 dB ustunde; vokal varken muzik ~3 dB kisilir."""
    vocal = vocal + 0.15 * kidsong._reverb(vocal, 0.9, seed=7)
    env = np.convolve(np.abs(vocal), np.ones(2205) / 2205, mode="same")
    active = env > 0.1 * env.max()
    m_rms = np.sqrt(np.mean(music[active] ** 2)) or 1e-6
    v_rms = np.sqrt(np.mean(vocal[active] ** 2)) or 1e-6
    vocal = vocal * (m_rms / v_rms) * 10 ** (4 / 20)
    duck = 1 - (1 - 10 ** (-3 / 20)) * np.clip(env / (0.1 * env.max()), 0, 1)
    duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
    return music * duck[:, None] + vocal[:, None] * np.array([0.71, 0.71])


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rep = ["== Vokal testi (deneme 3/3): DiffSinger Hanami + BigVGAN-v2, dogal perde ==", sing.CREDIT]
    samples.ensure()
    singer = sing.Singer()
    miss = sorted({w for lyr in LYRICS.values() for w in singer.missing_words(lyr)})
    rep.append(f"\n1) Sozlukte olmayan kelimeler: {miss or 'yok'}")
    if miss:
        raise SystemExit("\n".join(rep))
    voc = sing.Vocoder()

    # Kopya sentez: bankadaki GERCEK kayit -> mel -> BigVGAN. Vocoder+donusumun tavanini olcer.
    # (ToU/lisans: orijinal kayit degistirilip dagitilamaz -> sonuc SADECE sayi olarak raporlanir.)
    import librosa
    ref, _ = librosa.load(str(sing.ensure_voicebank() / "doremi.wav"), sr=sing.SR, mono=True)
    ref_mel = sing.ds_mel(ref, singer.fmin, singer.fmax)
    ref_y = voc(voc.ds_to_bigvgan(ref_mel, singer.fmin, singer.fmax))
    rep.append(f"   Kopya sentez (gercek kayit, doremi.wav): vocoder uyumu = "
               f"{mel_fit(ref_y, ref_mel, singer.fmin, singer.fmax):.2f}  <- vocoder+donusumun tavani")

    parts, dry = [], []
    for key, spk in SONGS:
        lyr = LYRICS[key]
        song = kidsong.arrange(key, len(lyr), lead=0.45)
        m = songs.MELODIES[key]
        lines = (m["lines"] * 2)[:len(lyr)]
        mel, f0, ph, slots = singer.render_mel(lyr, lines, song["line_starts"], song["beat"], speaker=spk)
        y = voc(voc.ds_to_bigvgan(mel, singer.fmin, singer.fmax))
        n = len(song["audio"])
        y = np.pad(y, (0, max(0, n - len(y))))[:n]
        audio_s = len(mel) * sing.HOP / sing.SR

        errs = np.abs(pitch_errors(y, slots)) if slots else np.array([])
        if not len(errs):
            errs = np.array([np.nan])
        note_times = [(0, 0, s["t0"]) for s in slots]
        mean_ms, max_ms, max_beat = music_test.onset_deviation(_band(y, 80, 1000), note_times, song["beat"])
        fit = mel_fit(y, mel, singer.fmin, singer.fmax)
        rep.append(f"\n--- {key} ({spk}), {len(slots)} hece, {audio_s:.1f} sn ses ---")
        rep.append(f"2) Perde: {len(errs)} nota olculdu, ortanca {np.median(errs):.0f} cent, "
                   f"%90 {np.percentile(errs, 90):.0f} cent, en kotu {errs.max():.0f} cent, "
                   f">50 cent: {(errs > 50).sum()}")
        rep.append(f"3) Ritim (tahmini): ortalama {mean_ms:.0f} ms, en kotu {max_ms:.0f} ms ({max_beat:.2f} vurus)")
        rep.append(f"4) Vocoder uyumu: ortalama |ln mel farki| = {fit:.2f} (0 = birebir)")
        voiced = mel.max(axis=1) > -3.0
        q = np.percentile(mel[voiced], [1, 10, 50, 90, 99]) if voiced.any() else [np.nan] * 5
        rep.append(f"   Model mel dagilimi (sesli kareler) %1/%10/%50/%90/%99: "
                   + " / ".join(f"{x:.1f}" for x in q) + f"; sessiz karelerde min {mel[~voiced].min() if (~voiced).any() else np.nan:.1f}")
        rep.append(f"5) Sure: perde modeli {singer.timing.get('pitch_s', 0):.1f} sn, akustik {singer.timing['acoustic_s']:.1f} sn, vocoder {voc.timing['vocoder_s']:.1f} sn "
                   f"({(singer.timing['acoustic_s'] + voc.timing['vocoder_s']) / audio_s:.2f} x gercek zaman)")
        rep.append("   Fonemler (ilk satir): " + " ".join(p for p, a, b in ph[:24]))
        cv, cm = clicks(y), clicks(song["audio"].mean(axis=1))
        def at(t):
            return next((p for p, a, b in ph if a <= t < b), "-")
        rep.append(f"7) Tik/cizirti: vokalde {len(cv)}, muzikte {len(cm)}")
        if cv:
            rep.append("   vokal: " + ", ".join(f"{t:.2f}sn[{at(t)}] +{d:.0f}dB" for t, d in cv[:15]))
        if cm:
            rep.append("   muzik: " + ", ".join(f"{t:.2f}sn +{d:.0f}dB" for t, d in cm[:15]))
        (OUT / "vocal_test_report.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")

        parts += [mix(song["audio"], y), np.zeros((samples.SR, 2))]
        dry += [y / (np.max(np.abs(y)) or 1.0) * 0.5, np.zeros(samples.SR)]

    music_test.write_wav_stereo(OUT / "vocal_test.wav", np.concatenate(parts))
    music_test.loudnorm(OUT / "vocal_test.wav", OUT / "vocal_test.mp3")
    d = np.concatenate(dry)
    music_test.write_wav_stereo(OUT / "vocal_test_dry.wav", np.stack([d, d], axis=1))
    music_test.loudnorm(OUT / "vocal_test_dry.wav", OUT / "vocal_test_dry.mp3")
    lufs, tp = music_test.measure_loudness(OUT / "vocal_test.mp3")
    rep.append(f"\n6) Ses yuksekligi: {lufs:.1f} LUFS, gercek tepe {tp:.1f} dBFS")
    text = "\n".join(rep)
    (OUT / "vocal_test_report.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
