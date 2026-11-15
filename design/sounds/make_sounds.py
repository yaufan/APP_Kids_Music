"""小小音波 (Little Wave): every sound in the app, made here from sine waves
and noise, so every one is ours: nothing recorded, nothing downloaded, every
tune written for this app (except the garbage truck, which plays the opening
of Bądarzewska's "A Maiden's Prayer" (1856), as Taiwan's garbage trucks do;
it has been public domain for well over a century, and the music box playing
it is synthesized here).

THE ONE RULE: everything the child can make sound is in ONE key and on ONE
tempo grid, so whatever is tapped or dragged sounds good together
(docs/design.md 「怎麼敲都好聽」):
- every pitched note is from C major pentatonic (C D E G A), no half steps;
- the animal band plays 2-bar loops (8 beats) at three tempos, 80, 100 and
  120 beats a minute, each rendered (not stretched) so the pitch stays put;
- at one tempo every animal's loop has EXACTLY the same number of samples
  (16,000 Hz: 96,000 / 76,800 / 64,000), so loops started together on the
  engine's clock stay together forever; whatever rings past the end of a
  loop wraps round to its start (seamless);
- the harmony under every loop is the same: bar 1 C, bar 2 A minor (both are
  all pentatonic notes), so the bass of any animal fits any other animal.

- Loops and music (WAV, 16,000 Hz): the ten animals x three tempos, the
  音樂木頭人 dance tune, the stage tune and the rest lullaby.
- Short sounds (WAV, 22,050 Hz): xylophone, drums, pots and pans (one per
  key), each animal's call, the bird on the stairs, the 聽聽看 sounds of
  Taiwanese daily life (no thunder, no ambulance), the freeze game's stings,
  the buttons.
- Voices (meow, woof, quack, yay...) are a buzz through formant filters.
- Every random choice uses a fixed seed: each run writes the same bytes.
- Every short sound is set to the same loudness as heard through a phone
  speaker (A-weighting, nothing under 250 Hz), plus or minus a few dB, with
  its peak at most 0.72 (about -3 dB). The band loops sit lower (peak at most
  0.42) so ten of them together still fit; the app plays them at 0.6.

The helpers (t_of, env, sweep, decay, lowpass, bandpass, highpass, norm,
partial, bell, marimba, place, tune_loop, resonator, voice, ease, glide,
pluck_bass, metal, shaker, kick, jingle, carry, celesta, chime, plink, clack,
a_weight, loudness, pizz, toy_horn, chirp, yay, clap, music_box, tidy,
phone_ready, level, write, seam, report, read) come from 小小生活家's
design/sounds/make_sounds.py (and through it from the other sibling apps).
New here: the ten animal voices and their parts, the xylophone, drums, pots
and pans, the Taiwanese street sounds and every tune.

    python3 design/sounds/make_sounds.py                  # writes app/assets/sounds/*.wav
    python3 design/sounds/make_sounds.py preview OUT.m4a  # and a listening preview
    python3 design/sounds/make_sounds.py tap xylo_0 ...    # only these (while working on one)
    python3 design/sounds/make_sounds.py band OUT.m4a     # all ten animals joining one by one
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import wave
import zlib

import numpy as np
from scipy.signal import lfilter, resample_poly

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "assets" / "sounds"
SR = 22050       # short sounds
LOOP_SR = 16000  # loops and music
LIMIT = 15_000_000  # bytes, the whole folder

# Notes (Hz).
NOTE = {f"{n}{o}": 440 * 2 ** ((k - 9) / 12 + o - 4)
        for o in range(0, 9) for k, n in enumerate("C C# D D# E F F# G G# A A# B".split())}

TARGET = -21.0  # dB, the loudness of a short sound at 0
MAX_PEAK = 0.72


# ---------------------------------------------------------------- helpers (from 小小生活家 and the other sibling apps)


def t_of(dur, sr=SR):
    return np.arange(int(dur * sr)) / sr


def env(n, attack=0.005, release=0.05, sr=SR):
    """Up quickly, down smoothly: no clicks at either end."""
    e = np.ones(n)
    a, r = max(1, min(n, int(attack * sr))), max(1, min(n, int(release * sr)))
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def sweep(f, sr=SR):
    """A sine whose frequency follows the array [f] (Hz per sample)."""
    return np.sin(2 * np.pi * np.cumsum(f) / sr)


def decay(n, tau, sr=SR):
    return np.exp(-np.arange(n) / (tau * sr))


def lowpass(x, cutoff, sr=SR):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec *= 1 / (1 + (freqs / cutoff) ** 4)
    return np.fft.irfft(spec, len(x))


def bandpass(x, lo, hi, sr=SR):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec *= 1 / (1 + (lo / np.maximum(freqs, 1)) ** 4) / (1 + (freqs / hi) ** 4)
    return np.fft.irfft(spec, len(x))


def highpass(x, cutoff, sr=SR):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec *= 1 / (1 + (cutoff / np.maximum(freqs, 1e-3)) ** 4)
    return np.fft.irfft(spec, len(x))


def norm(x):
    return x / max(1e-9, np.abs(x).max())


def partial(freq, t, sr):
    """A sine at [freq], or silence if it is too high for [sr] (it would fold
    back down as a wrong note)."""
    return np.sin(2 * np.pi * freq * t) if freq < 0.45 * sr else np.zeros_like(t)


def bell(freq, dur=0.5, sr=SR, bright=1.0):
    """A soft glockenspiel note: a few partials, the high ones dying first."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.35))
         + 0.35 * bright * partial(freq * 2.76, t, sr) * np.exp(-t / (dur * 0.12))
         + 0.15 * bright * partial(freq * 5.4, t, sr) * np.exp(-t / (dur * 0.06)))
    return x * env(len(t), 0.002, 0.03, sr)


def marimba(freq, dur=0.5, sr=SR):
    t = t_of(dur, sr)
    x = partial(freq, t, sr) * np.exp(-t / (dur * 0.3)) + 0.2 * partial(freq * 4, t, sr) * np.exp(-t / (dur * 0.05))
    return x * env(len(t), 0.003, 0.03, sr)


def place(total, parts, sr=SR):
    """[parts]: (start seconds, signal) mixed into [total] seconds."""
    out = np.zeros(int(total * sr))
    for start, sig in parts:
        i = int(start * sr)
        j = min(len(out), i + len(sig))
        out[i:j] += sig[: j - i]
    return out


def tune_loop(seconds, notes, sr=LOOP_SR):
    """[notes]: (start seconds, signal); what rings past [seconds] wraps to the start."""
    n = int(round(seconds * sr))
    tail = max(len(sig) + int(start * sr) for start, sig in notes) - n
    out = np.zeros(n + max(0, tail))
    for start, sig in notes:
        i = int(start * sr)
        out[i:i + len(sig)] += sig
    loop = out[:n].copy()
    if tail > 0:
        loop[:tail] += out[n:]
    return loop


def resonator(x, freq, bw, sr=SR, block=64):
    """A two-pole resonance at [freq] Hz (a number, or one per sample, for a
    sound that changes) of bandwidth [bw] Hz."""
    freq = np.broadcast_to(np.asarray(freq, dtype=float), x.shape)
    y, zi = np.zeros_like(x), np.zeros(2)
    r = np.exp(-np.pi * bw / sr)
    for i in range(0, len(x), block):
        th = 2 * np.pi * freq[i] / sr
        y[i:i + block], zi = lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x[i:i + block], zi=zi)
    return y


def voice(f0, formants, rng, breath=0.03, rough=0.0, sr=SR):
    """A voice at pitch [f0] (Hz per sample) through [formants]: (Hz or Hz
    per sample, bandwidth, gain). [rough] jitters the pitch, for a growl."""
    n = len(f0)
    if rough:
        f0 = f0 * (1 + rough * lowpass(rng.standard_normal(n), 60, sr) * 3)
    buzz = 2 * (np.cumsum(f0) / sr % 1) - 1 + breath * rng.standard_normal(n)
    out = np.zeros(n)
    for f, bw, gain in formants:
        y = resonator(buzz, f, bw, sr)
        out += gain * y / max(1e-9, np.abs(y).max())
    return lowpass(out, 3800, sr)  # soft, not a kazoo


def ease(u):
    """0 to 1, smoothly, over u in 0..1."""
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def glide(t, *points):
    """A value that moves smoothly between (time, value) [points]."""
    ts, vs = zip(*points)
    out = np.interp(t, ts, vs)
    return lowpass(out - out.mean(), 25) + out.mean() if len(t) > 64 else out


def pluck_bass(freq, dur=1.0, sr=LOOP_SR):
    """A plucked double bass: round, short, warm."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.35))
         + 0.45 * partial(freq * 2, t, sr) * np.exp(-t / (dur * 0.15))
         + 0.15 * partial(freq * 3, t, sr) * np.exp(-t / (dur * 0.08)))
    return x * env(len(t), 0.006, 0.08, sr)


def metal(freq, dur, sr=SR, ratios=(1, 1.59, 2.14, 2.65, 3.15), amps=(1, .6, .45, .3, .2), taus=(.5, .3, .2, .15, .1)):
    """A small metal ting (a bell, a coin): partials that are not
    whole-number multiples; [taus] are fractions of [dur]."""
    t = t_of(dur, sr)
    x = sum(a * partial(freq * r, t, sr) * np.exp(-t / (dur * k)) for r, a, k in zip(ratios, amps, taus))
    return x * env(len(t), 0.0008, 0.03, sr)


def shaker(rng, sr=LOOP_SR, dur=0.06, lo=3000, hi=7000):
    n = int(dur * sr)
    return norm(bandpass(rng.standard_normal(n), lo, hi, sr)) * env(n, 0.006, dur * 0.8, sr)


def kick(sr=LOOP_SR, dur=0.16):
    n = int(dur * sr)
    return sweep(np.geomspace(130, 55, n), sr) * decay(n, 0.05, sr) * env(n, 0.002, 0.04, sr)


def jingle(rng, dur=0.2, sr=SR):
    """A tambourine's little cymbals."""
    t = t_of(dur, sr)
    x = sum(rng.uniform(0.4, 1.0) * partial(f, t, sr) * np.exp(-t / rng.uniform(0.03, 0.07))
            for f in rng.uniform(4500, 9000, 8))
    x += 0.5 * norm(bandpass(rng.standard_normal(len(t)), 5000, 10000, sr)) * np.exp(-t / 0.02)
    return x * env(len(t), 0.001, 0.04, sr)


def carry(x, amount=0.3, lo=500, hi=3000, drive=2.5, sr=SR):
    """Phone speakers hardly play anything under about 300 Hz. For a low
    sound, add its own overtones (a soft saturation of it, kept to [lo]..[hi]
    Hz): a phone plays those, and the ear still hears the low note."""
    peak = max(1e-9, np.abs(x).max())
    over = bandpass(np.tanh(drive * x / peak), lo, hi, sr)
    return x + amount * peak * norm(over)


def celesta(freq, dur=1.0, sr=LOOP_SR):
    """A celesta: a felt hammer on a small steel bar over a wooden box. A
    sweet, round tone with a little of its octave, and a soft tick."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.3))
         + 0.25 * partial(freq * 2, t, sr) * np.exp(-t / (dur * 0.12))
         + 0.06 * partial(freq * 4.1, t, sr) * np.exp(-t / 0.02))
    return x * env(len(t), 0.0015, 0.05, sr)


def chime(freq, dur, sr=SR):
    """A soft, warm bell: whole-number partials (no glockenspiel clang), two
    tones a hair apart so it shimmers as it rings."""
    t = t_of(dur, sr)
    x = ((partial(freq, t, sr) + 0.5 * partial(freq * 1.003, t, sr)) * np.exp(-t / (dur * 0.38))
         + 0.28 * partial(freq * 2.0, t, sr) * np.exp(-t / (dur * 0.16))
         + 0.1 * partial(freq * 3.01, t, sr) * np.exp(-t / (dur * 0.07)))
    return x * env(len(t), 0.003, 0.08, sr)


def plink(freq, dur=0.25, sr=LOOP_SR):
    """A little glassy plink, like a bead dropped on a toy block."""
    t = t_of(dur, sr)
    x = partial(freq, t, sr) * np.exp(-t / 0.05) + 0.3 * partial(freq * 2.76, t, sr) * np.exp(-t / 0.012)
    return x * env(len(t), 0.0008, 0.03, sr)


def clack(rng, sr=LOOP_SR, dur=0.06):
    """Two wooden blocks knocked together: a short, hollow clack."""
    n = int(dur * sr)
    t = np.arange(n) / sr
    hit = rng.standard_normal(n) * np.exp(-t / 0.002)
    x = norm(resonator(hit, 1250, 120, sr)) + 0.6 * norm(resonator(hit, 2650, 200, sr))
    return x * np.exp(-t / 0.018) * env(n, 0.0005, 0.015, sr)


def a_weight(x, sr):
    """[x] as the ear hears it out of a phone: A-weighting (the ear is less
    sensitive to low and very high sounds) and nothing under about 250 Hz."""
    spec = np.fft.rfft(x)
    f2 = np.fft.rfftfreq(len(x), 1 / sr) ** 2
    ra = 12194 ** 2 * f2 ** 2 / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194 ** 2))
    phone = 1 / (1 + (250 ** 2 / np.maximum(f2, 1e-6)) ** 2)
    return np.fft.irfft(spec * ra * 1.2589 * phone, len(x))


def loudness(x, sr):
    """How loud [x] sounds, roughly, in dB: the weighted power in 200 ms
    windows (the ear adds up about that long, so a click sounds softer than
    a note as loud), over the windows within 20 dB of the loudest one."""
    y = a_weight(np.asarray(x, dtype=np.float64), sr) ** 2
    w, hop = int(0.2 * sr), int(0.025 * sr)
    y = np.concatenate([y, np.zeros(max(0, w - len(y)))])
    c = np.concatenate([[0], np.cumsum(y)])
    e = (c[w::hop] - c[:len(c) - w:hop]) / w
    return 10 * np.log10(max(1e-12, np.mean(e[e >= e.max() * 0.01])))


def pizz(freq, dur=0.5, sr=LOOP_SR, pos=0.14):
    """A pizzicato string, plucked with a finger: it rings only a moment,
    the high harmonics dying first; low notes ring a little longer."""
    t = t_of(dur, sr)
    tau = min(0.3, 0.07 + 50 / freq)
    x = np.zeros_like(t)
    for k in range(1, 9):
        x += abs(np.sin(np.pi * k * pos)) / k * partial(freq * k, t, sr) * np.exp(-t * (1 + 0.7 * (k - 1)) / tau)
    return x * env(len(t), 0.0012, 0.04, sr)


def toy_horn(freq, dur, sr=SR):
    """A soft toy trumpet: every harmonic, the high ones quieter, opening up
    as it speaks; a little vibrato on a long note."""
    t = t_of(dur, sr)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * ease((t - 0.15) / 0.2)
    ph = 2 * np.pi * np.cumsum(freq * vib) / sr
    opening = ease(t / 0.05)
    x = np.zeros_like(t)
    for k in range(1, 9):
        if freq * k < 0.4 * sr:
            x += (1 if k == 1 else opening) / k ** 1.4 * np.sin(k * ph)
    return lowpass(x, 3500, sr) * env(len(t), 0.015, min(0.1, dur * 0.4), sr)


def chirp(points, dur, sr=SR):
    """A bird's chirp: a pure whistle whose pitch follows (fraction of
    [dur], Hz) [points], swelling in and out."""
    t = t_of(dur, sr)
    fs, hz = zip(*points)
    f = np.interp(t / dur, fs, hz)
    return (sweep(f, sr) + 0.12 * sweep(2 * f, sr)) * np.sin(np.pi * t / dur) ** 1.2


def yay(rng, f, dur=0.32, size=1.15):
    """A small, happy "yay!" (ye-ay), jumping up."""
    t = t_of(dur)
    f0 = glide(t, (0, f), (0.08, f * 1.25), (dur, f * 1.05))
    f1 = np.interp(t, [0, 0.05, 0.2, dur], [300, 750, 700, 450]) * size
    f2 = np.interp(t, [0, 0.05, 0.2, dur], [2300, 1800, 1900, 2200]) * size
    return voice(f0, [(f1, 130, 1.0), (f2, 180, 0.55), (3000 * size, 300, 0.12)], rng, breath=0.1) * env(len(t), 0.02, 0.1)


def clap(rng, sr=LOOP_SR):
    """A soft hand clap: three quick slaps of air close together, and the
    clap itself."""
    n = int(0.12 * sr)
    shape = np.zeros(n)
    for k, d in enumerate((0, 0.008, 0.017, 0.026)):
        i = int(d * sr)
        shape[i:] += (0.6 if k < 3 else 1) * np.exp(-np.arange(n - i) / sr / (0.004 if k < 3 else 0.03))
    return norm(bandpass(rng.standard_normal(n), 900, 4000, sr) * shape) * env(n, 0.0005, 0.03, sr)


def music_box(freq, dur=1.4, sr=LOOP_SR):
    """A music box: a pin plucks a steel comb tooth. A sweet, pure note with a
    second tooth a hair out of tune (so it shimmers), the tooth's own high
    overtone (not a whole multiple) dying quickly, a touch of its octave
    from the wooden box, and the tiny tick of the pin."""
    t = t_of(dur, sr)
    x = ((partial(freq, t, sr) + 0.4 * partial(freq * 1.0025, t, sr)) * np.exp(-t / (dur * 0.33))
         + 0.22 * partial(freq * 2.0, t, sr) * np.exp(-t / (dur * 0.12))
         + 0.2 * partial(freq * 2.76, t, sr) * np.exp(-t / 0.05)
         + 0.07 * partial(freq * 5.4, t, sr) * np.exp(-t / 0.012)
         + 0.05 * partial(3100, t, sr) * np.exp(-t / 0.004))
    return x * env(len(t), 0.001, 0.06, sr)


def tidy(x, sr=SR):
    """A short sound: drop the silent end, then fade both ends so neither clicks."""
    x = np.asarray(x, dtype=np.float64)
    loud = np.nonzero(np.abs(x) > np.abs(x).max() * 1e-3)[0]
    x = x[: min(len(x), loud[-1] + int(0.01 * sr))]
    return x * env(len(x), 0.002, 0.012, sr)


def phone_ready(x, sr=SR):
    """Take out what a phone cannot play anyway (under 70 Hz), for more room
    under the peak. The filter works on the whole sound at once and wraps
    round, so pad it with silence on both sides first: what it rings before
    the start and after the end then stays out of the sound."""
    pad_ = int(0.1 * sr)
    return highpass(np.concatenate([np.zeros(pad_), x, np.zeros(pad_)]), 70, sr)[pad_:]


def level(x, offset, sr=SR):
    """[x] at the loudness TARGET + [offset] dB, unless that would put its
    peak over MAX_PEAK: then at MAX_PEAK. Returns the peak."""
    x = norm(x)
    return min(MAX_PEAK, 10 ** ((TARGET + offset - loudness(x, sr)) / 20))


def write(path, x, peak, sr):
    x = np.asarray(x, dtype=np.float64)
    x = x / max(1e-9, np.abs(x).max()) * peak
    data = np.round(x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())
    return data


def seam(data, sr):
    """A loop's seam, checked two ways: the jump from the last sample back to
    the first (beside the biggest step from one sample to the next in the
    20 ms either side of it: a click would stand out above them), and the
    sound over 3 kHz in the 20 ms around the seam (a click would show as a
    burst there) beside the loudest 20 ms anywhere else in the loop."""
    x = data.astype(np.float64)
    steps_ = np.abs(np.diff(x))
    jump = abs(x[0] - x[-1])
    half = len(x) // 2
    h = highpass(np.roll(x, half), 3000, sr) ** 2  # the seam now sits at [half]
    w = int(0.02 * sr)
    c = np.concatenate([[0], np.cumsum(h)])
    starts = np.arange(0, len(h) - w + 1, w // 2)
    at = half - w // 2
    here = c[at + w] - c[at]
    others = (c[starts + w] - c[starts])[np.abs(starts - at) >= w]
    near = np.concatenate([steps_[-w:], steps_[:w]]).max()  # the biggest step in the 20 ms either side
    return jump, near, here / max(1e-9, others.max())


def report(name, data, sr, loop, want=None):
    x = data.astype(np.float64) / 32767
    peak = np.abs(x).max()
    loud = loudness(x, sr)
    clipped = int(np.sum(np.abs(data) >= 32767))
    assert clipped == 0, name
    if loop:
        jump, near, burst_ = seam(data, sr)
        assert jump <= near and burst_ < 0.5, (name, jump, near, burst_)
        edge = f"seam jump {jump:3.0f} (biggest step near it {near:.0f}), seam highs {burst_:.2f} of the loudest elsewhere"
    else:
        edge = f"ends {int(data[0]):+d} / {int(data[-1]):+d}"
    short = "" if want is None or loud > want - 0.5 else f"  ({want - loud:.1f} dB under, held by the peak)"
    print(f"  {name:16s} {len(x) / sr:5.2f} s  {len(data) * 2 + 44:9,d} bytes  peak {peak:.2f}  "
          f"loudness {loud:6.1f} dB  clipped {clipped}  {edge}{short}")


def read(path):
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32767, w.getframerate()


def squash(x, drive=3.0):
    """A soft limiter for drums and other low thumps: their sharp first peak would otherwise keep them far quieter
    than everything else (the peak limit is reached long before the loudness)."""
    return np.tanh(drive * norm(x)) / np.tanh(drive)


def rng_for(name):
    """A seeded generator for one sound (its own, so changing one sound never changes another)."""
    return np.random.default_rng(zlib.crc32(name.encode()))


# ---------------------------------------------------------------- the music grid
SCALE = ("C", "D", "E", "G", "A")          # C major pentatonic
TEMPOS = {"slow": 80, "normal": 100, "fast": 120}
LOOP_BEATS = 8                             # two bars of 4/4


def loop_samples(bpm):
    """Samples in one band loop at [bpm] (exact: 96,000 / 76,800 / 64,000)."""
    n = LOOP_BEATS * 60 * LOOP_SR
    assert n % bpm == 0, bpm
    return n // bpm


def pentatonic(name):
    assert name[:-1] in SCALE, f"{name} is not in C major pentatonic"
    return NOTE[name]


# ---------------------------------------------------------------- the ten animal voices
# Each takes (freq Hz, how long the note may last in seconds, rng, sr) and returns one note.

def v_bear(f, dur, rng, sr=LOOP_SR):
    """小熊: a plucked double bass, a little slow vibrato, low."""
    d = min(0.9, dur)
    t = t_of(d, sr)
    x = pizz(f, d, sr, pos=0.2) + 0.25 * np.sin(2 * np.pi * f * t * (1 + 0.004 * np.sin(2 * np.pi * 5 * t))) * np.exp(-t / 0.25)
    return squash(carry(x * env(len(t), 0.004, 0.05, sr), 0.6, 300, 2000, sr=sr), 2.5)


def v_frog(f, dur, rng, sr=LOOP_SR):
    """青蛙: a buzzy "呱": a square-ish buzz that rattles (about 40 times a second) and drops a little."""
    d = 0.17
    t = t_of(d, sr)
    f0 = glide(t, (0, f * 1.12), (d, f * 0.9)) if len(t) > 64 else np.full(len(t), f)
    x = voice(f0, [(650, 180, 1.0), (1500, 260, 0.6), (2600, 400, 0.2)], rng, breath=0.25, rough=0.02, sr=sr)
    x *= 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * t))
    return lowpass(x, 3500, sr) * env(len(t), 0.004, 0.05, sr)


def v_bird(f, dur, rng, sr=LOOP_SR):
    """小鳥: a whistle that slides up into its note, with a little vibrato (like a flute)."""
    d = min(0.55, dur * 0.95)
    t = t_of(d, sr)
    fs = f * (1 - 0.12 * np.exp(-t / 0.025)) * (1 + 0.006 * np.sin(2 * np.pi * 6 * t) * ease((t - 0.12) / 0.1))
    ph = 2 * np.pi * np.cumsum(fs) / sr
    x = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.03 * np.sin(3 * ph)
    x += 0.04 * norm(bandpass(rng.standard_normal(len(t)), f, min(f * 3, 0.45 * sr), sr))
    return x * env(len(t), 0.012, min(0.15, d * 0.5), sr) * np.exp(-t / 0.6)


def v_cat(f, dur, rng, sr=LOOP_SR):
    """小貓: a long, nasal "喵～" that slides up then down (m-e-ow)."""
    d = min(1.9, dur * 0.92)
    t = t_of(d, sr)
    f0 = glide(t, (0, f * 0.86), (d * 0.3, f * 1.04), (d * 0.75, f), (d, f * 0.84))
    f1 = np.interp(t, [0, d * 0.15, d * 0.5, d], [350, 750, 800, 450])
    f2 = np.interp(t, [0, d * 0.15, d * 0.5, d], [1500, 1900, 1300, 900])
    x = voice(f0, [(f1, 140, 1.0), (f2, 200, 0.55), (2800, 300, 0.15)], rng, breath=0.05, sr=sr)
    return x * env(len(t), 0.05, min(0.35, d * 0.3), sr)


def v_dog(f, dur, rng, sr=LOOP_SR):
    """小狗: a short, round "汪"."""
    d = 0.16
    t = t_of(d, sr)
    f0 = glide(t, (0, f * 1.15), (0.05, f * 1.05), (d, f * 0.82)) if len(t) > 64 else np.full(len(t), f)
    x = voice(f0, [(np.interp(t, [0, 0.04, d], [400, 700, 500]), 160, 1.0), (1250, 220, 0.5), (2500, 300, 0.12)],
              rng, breath=0.12, rough=0.015, sr=sr)
    return x * env(len(t), 0.006, 0.06, sr)


def v_elephant(f, dur, rng, sr=LOOP_SR):
    """小象: a soft low toy horn "叭～"."""
    d = min(0.9, dur * 0.8)
    x = toy_horn(f, d, sr)
    return carry(x, 0.35, 300, 2200, sr=sr)


def v_blackbear(f, dur, rng, sr=LOOP_SR):
    """台灣黑熊: a big bass drum with a low, friendly "吼" over it."""
    d = 0.55
    t = t_of(d, sr)
    boom = np.zeros(len(t))
    k = kick(sr, 0.3) * 1.2
    boom[:len(k)] += k
    f0 = glide(t, (0, f * 1.6), (0.1, f * 2.0), (d, f * 1.5))
    growl = voice(f0, [(380, 120, 1.0), (800, 200, 0.5), (1800, 300, 0.12)], rng, breath=0.15, rough=0.06, sr=sr)
    growl *= env(len(t), 0.04, 0.2, sr) * 0.55
    return carry(boom + growl, 0.4, 300, 2000, sr=sr) * env(len(t), 0.002, 0.1, sr)


def v_leopard(f, dur, rng, sr=LOOP_SR):
    """石虎: a soft brush and shaker, "嘶～沙沙": short "沙" on the beats, a long "嘶" now and then."""
    d = min(0.35, dur * 0.9) if dur >= 0.45 else 0.07
    n = int(d * sr)
    t = np.arange(n) / sr
    x = norm(bandpass(rng.standard_normal(n), 2500, 7000, sr))
    shape = np.exp(-t / (0.02 if d < 0.1 else 0.12)) if d < 0.1 else np.sin(np.pi * t / d) ** 0.6
    return x * shape * env(n, 0.003, 0.02, sr)


def v_magpie(f, dur, rng, sr=LOOP_SR):
    """藍鵲: a short, bright "嘎" with a wood-block knock (like castanets)."""
    d = 0.12
    t = t_of(d, sr)
    f0 = glide(t, (0, f * 0.5), (d, f * 0.42)) if len(t) > 64 else np.full(len(t), f * 0.5)
    x = voice(f0, [(1300, 250, 1.0), (2600, 350, 0.6), (f, 200, 0.4)], rng, breath=0.2, rough=0.03, sr=sr)
    knock = np.zeros(len(t))
    c = clack(rng, sr, 0.05)
    knock[:len(c)] = c
    return (0.7 * norm(x) + 0.5 * knock) * env(len(t), 0.002, 0.04, sr)


def v_duck(f, dur, rng, sr=LOOP_SR):
    """小鴨: a nasal, harmonica-ish "呱"."""
    d = 0.15
    t = t_of(d, sr)
    f0 = glide(t, (0, f * 1.02), (d, f * 0.94)) if len(t) > 64 else np.full(len(t), f)
    x = voice(f0, [(1000, 150, 1.0), (1400, 200, 0.7), (2700, 300, 0.3)], rng, breath=0.05, sr=sr)
    x += 0.3 * norm(sweep(f0, sr))
    return x * env(len(t), 0.008, 0.05, sr)


# The parts: (beat, note, beats). Bar 1 is C, bar 2 A minor, for every animal.
ANIMALS = {
    "bear": (v_bear, [(0, "C3", 1), (1, "C3", 1), (2, "G2", 1), (3, "C3", 1),
                      (4, "A2", 1), (5, "A2", 1), (6, "E2", 1), (7, "A2", 1)]),
    "frog": (v_frog, [(0, "G3", .5), (1.5, "G3", .5), (2, "E3", .5), (3, "G3", .5),
                      (4, "G3", .5), (5.5, "G3", .5), (6, "E3", .5), (7, "G3", .5), (7.5, "A3", .5)]),
    "bird": (v_bird, [(0, "E5", 1), (1, "G5", 1), (2, "A5", 1.5), (4, "G5", 1), (5, "E5", 1), (6, "D5", 1.5)]),
    "cat": (v_cat, [(0, "G4", 3.5), (4, "E4", 3.5)]),
    "dog": (v_dog, [(0.5, "C4", .5), (2.5, "C4", .5), (3.5, "G4", .5),
                    (4.5, "A3", .5), (6.5, "A3", .5), (7.5, "E4", .5)]),
    "elephant": (v_elephant, [(0, "C3", 1.5), (2, "G2", 1.5), (4, "A2", 1.5), (6, "E3", 1.5)]),
    "blackbear": (v_blackbear, [(0, "C2", 2), (4, "A1", 2)]),
    "leopard": (v_leopard, [(b / 2, None, 1 if b in (7, 15) else .5) for b in range(16) if b not in (8,)]),
    "magpie": (v_magpie, [(3, "C6", .5), (3.5, "A5", .5), (7, "G5", .5), (7.5, "E5", .5)]),
    "duck": (v_duck, [(0.5, "E4", .5), (1.5, "G4", .5), (2.5, "E4", .5), (3.5, "G4", .5),
                      (4.5, "C4", .5), (5.5, "E4", .5), (6.5, "C4", .5), (7.5, "E4", .5)]),
}
# The order the app shows them in (the first six are in the free version).
ANIMAL_ORDER = ("bear", "frog", "bird", "cat", "dog", "elephant", "blackbear", "leopard", "magpie", "duck")
assert set(ANIMAL_ORDER) == set(ANIMALS)
LOOP_LOUD = -28.0   # dB, one animal alone
LOOP_PEAK = 0.42


def band_loop(animal, bpm, sr=LOOP_SR):
    make, part = ANIMALS[animal]
    beat = 60 / bpm
    rng = rng_for(f"band_{animal}")
    notes = []
    for b, name, beats in part:
        f = pentatonic(name) if name else 0.0
        notes.append((b * beat, make(f, beats * beat, rng, sr)))
    x = tune_loop(LOOP_BEATS * beat, notes, sr)
    assert len(x) == loop_samples(bpm), (animal, bpm, len(x))
    return x


def call(animal):
    """Tapping an animal on the stage: one note of its voice (22,050 Hz)."""
    make, part = ANIMALS[animal]
    rng = rng_for(f"call_{animal}")
    note = {"bear": "C3", "frog": "G3", "bird": "G5", "cat": "G4", "dog": "C4", "elephant": "C3",
            "blackbear": "C2", "leopard": None, "magpie": "A5", "duck": "E4"}[animal]
    f = pentatonic(note) if note else 0.0
    if animal == "leopard":
        x = place(0.6, [(0, make(0, 0.5, rng, SR)), (0.38, make(0, 0.3, rng, SR)), (0.48, make(0, 0.3, rng, SR))])
    elif animal in ("frog", "dog", "duck", "magpie"):
        x = place(0.5, [(0, make(f, 0.3, rng, SR)), (0.22, make(f * (1.122 if animal != "magpie" else 0.89), 0.3, rng, SR))])
    else:
        x = make(f, 0.8, rng, SR)
    return x


# ---------------------------------------------------------------- the keys: xylophone, drums, pots and pans
XYLO = ("C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6")


def xylo(name):
    """A wooden bar: the tone, its overtone 2.76 times up (as a real bar has), a little knock; gone in 0.6 s."""
    f = pentatonic(name)
    rng = rng_for(f"xylo_{name}")
    d = 0.9
    t = t_of(d)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.2)
         + 0.35 * partial(f * 2.76, t, SR) * np.exp(-t / 0.05)
         + 0.08 * partial(f * 5.4, t, SR) * np.exp(-t / 0.015))
    knock = 0.25 * norm(bandpass(rng.standard_normal(len(t)), 800, 4000)) * np.exp(-t / 0.004)
    return (x + knock) * env(len(t), 0.001, 0.05)


def drum(i):
    """Five drums: a big bass drum, a low and a high tom (tuned to C and G), a snare, a tambourine."""
    rng = rng_for(f"drum_{i}")
    if i == 0:
        d = 0.6
        t = t_of(d)
        x = sweep(np.geomspace(150, 50, len(t))) * np.exp(-t / 0.18)
        x += 0.3 * norm(lowpass(rng.standard_normal(len(t)), 900)) * np.exp(-t / 0.01)
        return squash(carry(x, 0.9, 250, 1800), 4)
    if i in (1, 2):
        f = pentatonic("G3" if i == 1 else "C4")
        d = 0.5
        t = t_of(d)
        x = sweep(f * (1 + 0.5 * np.exp(-t / 0.03))) * np.exp(-t / 0.16) + 0.3 * partial(f * 1.6, t, SR) * np.exp(-t / 0.05)
        x += 0.25 * norm(bandpass(rng.standard_normal(len(t)), 300, 3000)) * np.exp(-t / 0.012)
        return squash(carry(x, 0.6, 300, 2200), 3)
    if i == 3:
        d = 0.32
        t = t_of(d)
        x = 0.6 * np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.05)
        x += norm(bandpass(rng.standard_normal(len(t)), 1500, 8000)) * np.exp(-t / 0.07)
        return squash(x * env(len(t), 0.001, 0.04), 2.5)
    return squash(jingle(rng, 0.4), 2.5)


POTS = ("pot", "lid", "bowl", "cup", "spoon")


def pot(i):
    """Pots and pans (what every kitchen has): a pot and a lid ring like metal (partials that do not line up), a bowl
    is clean (two partials), a cup is short, a spoon on a table is a tiny tink."""
    rng = rng_for(f"pot_{i}")
    kind = POTS[i]
    if kind == "pot":
        x = metal(pentatonic("G4"), 1.2, ratios=(1, 1.5, 2.3, 3.1, 4.2), amps=(1, .7, .5, .35, .2), taus=(.5, .35, .25, .15, .1))
        x[:400] += 0.3 * norm(bandpass(rng.standard_normal(400), 1000, 5000)) * np.exp(-np.arange(400) / 60)
        return x
    if kind == "lid":
        return metal(pentatonic("G4"), 1.4, ratios=(1, 1.5, 2.3, 3.1, 3.9), amps=(1, .8, .6, .4, .3), taus=(.6, .45, .3, .2, .15))
    if kind == "bowl":
        d = 1.0
        t = t_of(d)
        f = pentatonic("E5")
        return (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.35) + 0.3 * partial(f * 2.7, t, SR) * np.exp(-t / 0.12)) * env(len(t), 0.001, 0.05)
    if kind == "cup":
        d = 0.5
        t = t_of(d)
        f = pentatonic("A5")
        x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.08) + 0.4 * partial(f * 2.3, t, SR) * np.exp(-t / 0.03)
        x += 0.2 * norm(bandpass(rng.standard_normal(len(t)), 2000, 7000)) * np.exp(-t / 0.003)
        return x * env(len(t), 0.0008, 0.04)
    d = 0.35
    t = t_of(d)
    f = pentatonic("C6")
    x = 0.8 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.06) + 0.4 * partial(f * 2.1, t, SR) * np.exp(-t / 0.03)
    x += 0.6 * norm(bandpass(rng.standard_normal(len(t)), 2500, 9000)) * np.exp(-t / 0.002)
    return x * env(len(t), 0.0005, 0.03)


# ---------------------------------------------------------------- 高低快慢: the bird on the stairs, loud and soft
STAIRS = ("C5", "D5", "E5", "G5", "A5")


def stair_bird(i):
    """The bird on step [i]: a happy two-part tweet on that step's note."""
    f = pentatonic(STAIRS[i])
    a = chirp([(0, f * 0.85), (0.4, f * 1.02), (1, f)], 0.16)
    b = chirp([(0, f * 0.95), (0.5, f * 1.03), (1, f)], 0.28)
    return place(0.5, [(0, a), (0.17, b)])


def elephant_loud():
    """大聲: the elephant's big trumpet, "叭～～"."""
    rng = rng_for("loud")
    d = 1.0
    t = t_of(d)
    f0 = glide(t, (0, 260), (0.12, 330), (0.7, 330), (d, 300))
    x = voice(f0, [(700, 200, 1.0), (1300, 250, 0.8), (2600, 350, 0.4)], rng, breath=0.05, sr=SR)
    return x * env(len(t), 0.04, 0.25)


def mouse_soft():
    """小聲: a tiny mouse, "吱吱" (sits softer than everything else)."""
    a = chirp([(0, 2200), (0.5, 2700), (1, 2400)], 0.09)
    return place(0.42, [(0, a), (0.14, a), (0.28, a * 0.8)])


# ---------------------------------------------------------------- 音樂木頭人
def freeze_stop():
    """停！: a quick slide down on the xylophone and a soft "咚"."""
    rng = rng_for("freeze_stop")
    parts = [(i * 0.045, xylo(n) * (1 - i * 0.12)) for i, n in enumerate(("A5", "G5", "E5", "D5", "C5"))]
    k = drum(0) * 0.7
    parts.append((0.26, k))
    return place(0.95, parts) * (1 + 0 * rng.standard_normal(1))


def freeze_go():
    """Off again: a quick run up."""
    return place(0.75, [(i * 0.05, xylo(n) * (0.6 + i * 0.08)) for i, n in enumerate(("C5", "D5", "E5", "G5", "A5", "C6"))])


def shh():
    """噓～: a soft breath through the teeth."""
    rng = rng_for("shh")
    d = 0.7
    n = int(d * SR)
    t = np.arange(n) / SR
    x = norm(bandpass(rng.standard_normal(n), 2500, 6500))
    return x * np.sin(np.pi * t / d) ** 0.8


def cheer():
    """好棒！: three small yays and clapping."""
    rng = rng_for("cheer")
    parts = [(0.0, yay(rng, 420)), (0.06, yay(rng, 520, size=1.25)), (0.12, yay(rng, 360, size=1.05))]
    for i in range(10):
        parts.append((0.1 + i * 0.09 + rng.uniform(0, 0.03), clap(rng, SR) * rng.uniform(0.3, 0.6)))
    return place(1.3, parts)


# ---------------------------------------------------------------- 聽聽看: Taiwan's everyday sounds
def ls_garbage():
    """The garbage truck: a music box playing the opening of 〈少女的祈禱〉 (A Maiden's Prayer)."""
    beat = 0.36
    tune = [("G4", 1), ("C5", 1.5), ("B4", .5), ("A4", .5), ("G4", .5), ("F4", 1), ("E4", .5), ("D4", .5),
            ("C4", 1), ("D4", .5), ("E4", .5), ("F4", .5), ("G4", .5), ("A4", 1.5), ("G4", .5), ("F4", .5), ("E4", .5),
            ("D4", 2)]
    parts, b = [], 0.0
    for name, beats in tune:
        parts.append((b * beat, music_box(NOTE[name], 1.2, SR)))
        parts.append((b * beat, 0.35 * music_box(NOTE[name] * 2, 0.6, SR)))
        b += beats
    for i, (name, at) in enumerate((("C3", 1), ("G3", 5), ("F3", 9), ("G3", 13))):
        parts.append((at * beat, 0.4 * music_box(NOTE[name], 1.4, SR)))
    x = place(b * beat + 1.0, parts)
    t = t_of(len(x) / SR)
    return x * (0.75 + 0.25 * np.sin(2 * np.pi * 0.7 * t)) * env(len(x), 0.05, 0.6)  # a truck passing


def ls_scooter():
    """A scooter going by: "噗噗噗" (a small engine firing, revving up and away)."""
    rng = rng_for("ls_scooter")
    d = 2.4
    t = t_of(d)
    fire = glide(t, (0, 28), (0.6, 34), (1.4, 46), (d, 40))
    ph = np.cumsum(fire) / SR
    pulses = np.maximum(0, np.sin(2 * np.pi * ph)) ** 6
    noise = bandpass(rng.standard_normal(len(t)), 150, 1800)
    x = lowpass(pulses * (1 + 0.6 * norm(noise)), 1600) + 0.25 * norm(bandpass(rng.standard_normal(len(t)), 900, 3000)) * 0.2
    x = carry(x, 0.5, 300, 2400)
    return x * glide(t, (0, 0.3), (0.9, 1.0), (1.6, 1.0), (d, 0.25)) * env(len(t), 0.05, 0.3)


def ls_mrt():
    """The MRT doors closing: a run of quick "嗶" beeps, then the doors."""
    rng = rng_for("ls_mrt")
    parts = []
    for i in range(7):
        n = int(0.11 * SR)
        t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * 1000 * t) + 0.3 * np.sin(2 * np.pi * 3000 * t)) * env(n, 0.004, 0.02)
        parts.append((i * 0.19, x))
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    thud = norm(lowpass(rng.standard_normal(n), 400)) * np.exp(-t / 0.05)
    parts.append((1.45, carry(thud, 0.4, 300, 1500) * 0.8))
    return place(1.9, parts)


def ls_rain():
    """Rain: a soft hiss and drops."""
    rng = rng_for("ls_rain")
    d = 2.6
    n = int(d * SR)
    x = 0.5 * norm(bandpass(rng.standard_normal(n), 1500, 7000))
    for _ in range(90):
        at = rng.uniform(0, d - 0.1)
        f = rng.uniform(1800, 4200)
        dur = 0.035
        tt = t_of(dur)
        drop = np.sin(2 * np.pi * np.cumsum(np.geomspace(f, f * 1.5, len(tt))) / SR) * np.sin(np.pi * tt / dur)
        i = int(at * SR)
        x[i:i + len(drop)] += rng.uniform(0.3, 0.9) * drop
    return x * env(n, 0.3, 0.6)


def ls_temple():
    """The temple: two deep drum beats, then the big bell."""
    parts = []
    for at, a in ((0, 1.0), (0.55, 0.8), (1.1, 0.9)):
        d = 0.9
        t = t_of(d)
        x = sweep(80 * (1 + 0.2 * np.exp(-t / 0.05))) * np.exp(-t / 0.35) + 0.4 * partial(140, t, SR) * np.exp(-t / 0.15)
        parts.append((at, a * squash(carry(x, 0.7, 250, 1500), 3)))
    bell_ = metal(NOTE["G3"], 2.2, ratios=(1, 2.0, 2.76, 3.4, 5.1), amps=(1, .6, .5, .3, .2), taus=(.5, .4, .25, .15, .1))
    parts.append((1.75, 0.9 * bell_))
    return squash(place(3.6, parts), 2)


def ls_bike():
    """A bicycle bell: "叮鈴鈴" twice."""
    parts = []
    for k in range(2):
        for i in range(3):
            parts.append((k * 0.55 + i * 0.06, metal(2600, 0.5, ratios=(1, 1.47, 2.1), amps=(1, .7, .3), taus=(.5, .3, .2)) * (1 - i * 0.2)))
    return place(1.5, parts)


def ls_crossing():
    """A level crossing: two bells taking turns, "噹、噹、噹"."""
    parts = []
    for i in range(8):
        f = 740 if i % 2 == 0 else 622
        parts.append((i * 0.3, metal(f, 0.5, ratios=(1, 2.4, 3.9), amps=(1, .5, .25), taus=(.5, .25, .1))))
    return place(2.8, parts)


def ls_ricecooker():
    """The rice cooker: done, "喀"! (a click and a little spring), then a puff of steam."""
    rng = rng_for("ls_ricecooker")
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    click = norm(resonator(rng.standard_normal(n) * np.exp(-t / 0.003), 1800, 200)) + 0.5 * np.sin(2 * np.pi * 700 * t) * np.exp(-t / 0.02)
    spring = metal(1350, 0.35, ratios=(1, 1.9), amps=(1, .3), taus=(.4, .2)) * 0.3
    m = int(1.0 * SR)
    tt = np.arange(m) / SR
    steam = 0.25 * norm(bandpass(rng.standard_normal(m), 2500, 8000)) * np.sin(np.pi * tt / 1.0) ** 2
    return place(1.7, [(0.05, squash(click, 2.5)), (0.07, spring), (0.6, steam)])


def ls_stirfry():
    """Stir-frying: the sizzle "滋～" and the spatula on the wok."""
    rng = rng_for("ls_stirfry")
    d = 2.4
    n = int(d * SR)
    t = np.arange(n) / SR
    crackle = norm(bandpass(rng.standard_normal(n), 2500, 9000)) * (0.5 + 0.5 * (rng.random(n) > 0.995))
    sizzle = crackle * glide(t, (0, 0), (0.15, 1.0), (1.8, 0.8), (d, 0.3))
    parts = [(0, sizzle * env(n, 0.05, 0.4))]
    for at in (0.5, 0.9, 1.35, 1.7):
        parts.append((at, 0.6 * metal(1900, 0.25, ratios=(1, 1.6, 2.4), amps=(1, .6, .3), taus=(.3, .2, .1))))
    return place(d, parts)


def ls_cat():
    rng = rng_for("ls_cat")
    return place(1.7, [(0, v_cat(NOTE["G4"], 0.8, rng, SR)), (0.9, v_cat(NOTE["A4"], 0.75, rng, SR))])


def ls_dog():
    rng = rng_for("ls_dog")
    return place(1.0, [(0, v_dog(NOTE["G3"], 0.2, rng, SR)), (0.22, v_dog(NOTE["G3"], 0.2, rng, SR)), (0.6, v_dog(NOTE["A3"], 0.2, rng, SR))])


def ls_frog():
    rng = rng_for("ls_frog")
    parts = []
    for i, at in enumerate((0, 0.2, 0.7, 0.9, 1.1)):
        parts.append((at, v_frog(NOTE["E3"] * (1.0 if i % 2 == 0 else 1.06), 0.2, rng, SR)))
    return place(1.5, parts)


# ---------------------------------------------------------------- the buttons and the little happenings
def ui_tap():
    rng = rng_for("tap")
    return place(0.12, [(0, plink(NOTE["G5"], 0.12, SR) * 0.8), (0, 0.3 * clack(rng, SR, 0.03))])


def ui_back():
    return place(0.4, [(0, xylo("G5") * 0.6), (0.08, xylo("C5") * 0.6)])


def ui_open():
    return place(0.8, [(i * 0.07, xylo(n) * 0.7) for i, n in enumerate(("C5", "E5", "G5", "C6"))])


def ui_lock():
    """A locked toy: a soft, curious "嗯？" (two low notes going up), never a buzzer."""
    rng = rng_for("lock")
    d = 0.45
    t = t_of(d)
    f0 = glide(t, (0, 230), (0.2, 230), (d, 300))
    x = voice(f0, [(300, 100, 1.0), (900, 150, 0.2)], rng, breath=0.04, sr=SR)
    return lowpass(x, 1500) * env(len(t), 0.04, 0.12)


def ui_pop():
    """A balloon: "啵", and a note floats up."""
    rng = rng_for("pop")
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    burst = norm(bandpass(rng.standard_normal(n), 400, 5000)) * np.exp(-t / 0.008)
    return place(0.8, [(0, burst), (0.05, xylo("E6") * 0.5), (0.15, xylo("A5") * 0.4)])


def ui_applause():
    """The audience: clapping and a few small yays."""
    rng = rng_for("applause")
    parts = []
    for i in range(26):
        parts.append((rng.uniform(0, 1.3), clap(rng, SR) * rng.uniform(0.25, 0.6)))
    parts += [(0.2, 0.6 * yay(rng, 480)), (0.45, 0.5 * yay(rng, 400, size=1.05)), (0.7, 0.5 * yay(rng, 540, size=1.25))]
    x = place(1.5, parts)
    return x * env(len(x), 0.05, 0.4)


def ui_sparkle():
    rng = rng_for("sparkle")
    parts = [(i * 0.05 + rng.uniform(0, 0.02), plink(NOTE[n], 0.3, SR) * 0.6) for i, n in enumerate(("G6", "C7", "E7", "A6", "D7"))]
    return place(0.6, parts)


def ui_join():
    """An animal lands on its spot: a little "啵噔" up."""
    t = t_of(0.25)
    f = np.geomspace(300, 700, len(t))
    x = sweep(f) * np.sin(np.pi * t / 0.25)
    return place(0.5, [(0, x * 0.6), (0.18, xylo("G5") * 0.6)])


def ui_leave():
    t = t_of(0.25)
    f = np.geomspace(600, 260, len(t))
    return sweep(f) * np.sin(np.pi * t / 0.25)


def ui_slow():
    """The snail: a slow slide down."""
    return place(1.0, [(i * 0.16, xylo(n) * 0.6) for i, n in enumerate(("A5", "G5", "E5", "D5", "C5"))])


def ui_fast():
    """The rabbit: a quick run up."""
    return place(0.5, [(i * 0.04, xylo(n) * 0.6) for i, n in enumerate(("C5", "D5", "E5", "G5", "A5", "C6"))])


def ui_right():
    rng = rng_for("right")
    return place(0.9, [(0, yay(rng, 460)), (0.05, xylo("C6") * 0.4), (0.12, xylo("E6") * 0.4), (0.19, xylo("G5") * 0.4)])


def ui_rec_start():
    return place(0.35, [(0, plink(NOTE["C6"], 0.15, SR)), (0.12, plink(NOTE["G6"], 0.2, SR))])


def ui_rec_stop():
    return place(0.35, [(0, plink(NOTE["G6"], 0.15, SR)), (0.12, plink(NOTE["C6"], 0.2, SR))])


def ui_tick():
    rng = rng_for("tick")
    return clack(rng, SR, 0.05)


def ui_light():
    """The spotlight changes colour: a soft shimmer."""
    d = 0.7
    t = t_of(d)
    x = sum(np.sin(2 * np.pi * NOTE[n] * t) * (1 + 0.5 * np.sin(2 * np.pi * 6 * t)) for n in ("C6", "E6", "G6")) / 3
    return x * np.sin(np.pi * t / d)


def ui_lights_off():
    """One neon light going out: a soft click and a low hum dying."""
    rng = rng_for("lights_off")
    n = int(0.03 * SR)
    click = norm(bandpass(rng.standard_normal(n), 1500, 5000)) * np.exp(-np.arange(n) / SR / 0.004)
    d = 0.5
    t = t_of(d)
    hum = (np.sin(2 * np.pi * 330 * t) + 0.3 * np.sin(2 * np.pi * 660 * t)) * np.exp(-t / 0.12)
    return place(0.55, [(0, 0.6 * click), (0.01, 0.5 * hum)])


def ui_night():
    """Good night: a few soft chimes going down."""
    return place(2.0, [(i * 0.35, chime(NOTE[n], 1.2, SR) * (1 - i * 0.12)) for i, n in enumerate(("E5", "D5", "C5", "A4"))])


# ---------------------------------------------------------------- the tunes (16,000 Hz loops)
def notes_of(tune, beat):
    """[(note or None, beats)] -> [(seconds, note, seconds long)]."""
    out, b = [], 0.0
    for name, beats in tune:
        if name:
            out.append((b * beat, name, beats * beat))
        b += beats
    return out, b


def freeze_music():
    """音樂木頭人: a bouncy dance tune, 100 beats a minute, eight bars, all pentatonic (marimba lead, plucked bass,
    a soft kick, a shaker and a clap)."""
    bpm = 100
    beat = 60 / bpm
    rng = rng_for("freeze_music")
    tune = [("E5", 1), ("G5", 1), ("A5", .5), ("G5", .5), ("E5", 1),
            ("C5", 1), ("E5", 1), ("D5", 2),
            ("D5", 1), ("E5", .5), ("G5", .5), ("A5", 1), ("G5", 1),
            ("E5", 1), ("D5", 1), ("C5", 2),
            ("G5", 1), ("A5", 1), ("C6", .5), ("A5", .5), ("G5", 1),
            ("E5", 1), ("G5", 1), ("A5", 2),
            ("G5", .5), ("E5", .5), ("D5", 1), ("E5", .5), ("D5", .5), ("C5", 1),
            ("D5", 2), (None, 2)]
    lead, total = notes_of(tune, beat)
    assert total == 32
    roots = ("C3", "A2", "D3", "G2") * 2
    fifth = {"C3": "G3", "A2": "E3", "D3": "A3", "G2": "D3"}
    parts = [(s, 0.9 * marimba(NOTE[n], max(0.4, d), LOOP_SR)) for s, n, d in lead]
    parts += [(s, 0.25 * bell(NOTE[n] * 2, 0.4, LOOP_SR, 0.3)) for s, n, d in lead]
    for bar, r in enumerate(roots):
        for b in range(4):
            n = r if b % 2 == 0 else fifth[r]
            parts.append(((bar * 4 + b) * beat, 0.7 * pizz(NOTE[n], 0.5, LOOP_SR)))
            if b % 2 == 0:
                parts.append(((bar * 4 + b) * beat, 0.5 * kick(LOOP_SR, 0.16)))
            else:
                parts.append(((bar * 4 + b) * beat, 0.25 * clap(rng, LOOP_SR)))
            for h in (0, 0.5):
                parts.append(((bar * 4 + b + h) * beat, 0.12 * shaker(rng, LOOP_SR, 0.05)))
    return tune_loop(32 * beat, parts, LOOP_SR)


def stage_music():
    """The stage (home): a gentle celesta tune over a soft pad, 84 beats a minute, eight bars."""
    bpm = 84
    beat = 60 / bpm
    tune = [("E5", 2), ("D5", 1), ("C5", 1), ("D5", 2), ("E5", 2),
            ("G5", 2), ("A5", 1), ("G5", 1), ("E5", 4),
            ("A5", 2), ("G5", 1), ("E5", 1), ("D5", 2), ("C5", 2),
            ("D5", 2), ("E5", 1), ("D5", 1), ("C5", 4)]
    lead, total = notes_of(tune, beat)
    assert total == 32
    parts = [(s, celesta(NOTE[n], max(0.8, d), LOOP_SR)) for s, n, d in lead]
    chords = (("C4", "E4", "G4"), ("A3", "C4", "E4")) * 4
    for bar, ch in enumerate(chords):
        for b in range(4):
            for k, n in enumerate(ch):
                parts.append(((bar * 4 + b + k * 0.02) * beat, 0.16 * music_box(NOTE[n], 0.9, LOOP_SR)))
        parts.append((bar * 4 * beat, 0.35 * pluck_bass(NOTE[ch[0]] / 2, 1.5, LOOP_SR)))
    return tune_loop(32 * beat, parts, LOOP_SR)


def rest_music():
    """Resting: a slow music-box lullaby in three, 66 beats a minute, eight bars."""
    bpm = 66
    beat = 60 / bpm
    tune = [("G4", 1), ("E4", 1), ("G4", 1), ("A4", 2), ("G4", 1), ("E4", 2), ("D4", 1), ("C4", 3),
            ("D4", 1), ("E4", 1), ("G4", 1), ("A4", 2), ("G4", 1), ("E4", 1), ("D4", 1), ("E4", 1), ("C4", 3)]
    lead, total = notes_of(tune, beat)
    assert total == 24
    parts = [(s, music_box(NOTE[n], 1.8, LOOP_SR)) for s, n, d in lead]
    for bar in range(8):
        r = ("C3", "A2")[bar % 2]
        parts.append((bar * 3 * beat, 0.35 * music_box(NOTE[r], 2.0, LOOP_SR)))
    return tune_loop(24 * beat, parts, LOOP_SR)


# ---------------------------------------------------------------- the catalogue
# name: (maker, loudness offset in dB, longest seconds)
EFFECTS = {}
for _i, _n in enumerate(XYLO):
    EFFECTS[f"xylo_{_i}"] = (lambda n=_n: xylo(n), 0, 1.0)
for _i in range(5):
    EFFECTS[f"drum_{_i}"] = (lambda i=_i: drum(i), 0, 1.0)
    EFFECTS[f"pot_{_i}"] = (lambda i=_i: pot(i), -1, 1.5)
    EFFECTS[f"stair_{_i}"] = (lambda i=_i: stair_bird(i), -1, 0.6)
for _a in ANIMAL_ORDER:
    EFFECTS[f"call_{_a}"] = (lambda a=_a: call(a), 0, 1.0)
EFFECTS.update({
    "loud": (elephant_loud, 2, 1.1),
    "soft": (mouse_soft, -9, 0.5),
    "freeze_stop": (freeze_stop, 1, 1.0),
    "freeze_go": (freeze_go, -1, 0.8),
    "shh": (shh, -4, 0.8),
    "cheer": (cheer, 0, 1.4),
    "ls_garbage": (ls_garbage, -1, 6.5),
    "ls_scooter": (ls_scooter, 0, 2.5),
    "ls_mrt": (ls_mrt, -2, 2.0),
    "ls_rain": (ls_rain, -3, 2.7),
    "ls_temple": (ls_temple, 0, 3.7),
    "ls_bike": (ls_bike, -2, 1.6),
    "ls_crossing": (ls_crossing, -2, 2.9),
    "ls_ricecooker": (ls_ricecooker, -1, 1.8),
    "ls_stirfry": (ls_stirfry, -2, 2.5),
    "ls_cat": (ls_cat, 0, 1.8),
    "ls_dog": (ls_dog, 0, 1.1),
    "ls_frog": (ls_frog, 0, 1.6),
    "tap": (ui_tap, -5, 0.2),
    "back": (ui_back, -4, 0.5),
    "open": (ui_open, -3, 0.9),
    "lock": (ui_lock, -4, 0.5),
    "pop": (ui_pop, -2, 0.9),
    "applause": (ui_applause, -1, 1.6),
    "sparkle": (ui_sparkle, -4, 0.7),
    "join": (ui_join, -3, 0.6),
    "leave": (ui_leave, -4, 0.3),
    "slow": (ui_slow, -3, 1.1),
    "fast": (ui_fast, -3, 0.6),
    "right": (ui_right, -1, 1.0),
    "rec_start": (ui_rec_start, -4, 0.4),
    "rec_stop": (ui_rec_stop, -4, 0.4),
    "tick": (ui_tick, -7, 0.1),
    "light": (ui_light, -5, 0.8),
    "lights_off": (ui_lights_off, -6, 0.6),
    "night": (ui_night, -3, 2.1),
})

# name: (maker, loudness in dB) — whole tunes, 8 to 12 dB under the short sounds.
MUSIC = {
    "music_freeze": (freeze_music, -29.0),
    "music_stage": (stage_music, -31.0),
    "music_rest": (rest_music, -33.0),
}


def loop_level(x, want, peak):
    x = norm(x)
    return min(peak, 10 ** ((want - loudness(x, LOOP_SR)) / 20))


def loop_report(name, data, sr):
    x = data.astype(np.float64) / 32767
    clipped = int(np.sum(np.abs(data) >= 32767))
    assert clipped == 0, name
    jump = abs(x[0] - x[-1])
    w = int(0.02 * sr)
    steps_ = np.abs(np.diff(x))
    near = np.concatenate([steps_[-w:], steps_[:w]]).max()
    assert jump <= max(near, 1e-3), (name, jump, near)
    print(f"  {name:22s} {len(x) / sr:5.2f} s  {len(x):7d} samples  {len(data) * 2 + 44:9,d} bytes  "
          f"peak {np.abs(x).max():.2f}  loudness {loudness(x, sr):6.1f} dB  seam jump {jump * 32767:4.0f} (step near it {near * 32767:.0f})")


def band_names():
    return [f"band_{a}_{t}" for a in ANIMAL_ORDER for t in TEMPOS]


def preview(path, gap=0.5):
    """A listening preview: each tune (6 s), each animal alone (one loop), then every short sound."""
    path = pathlib.Path(path)
    sr, pieces = 22050, []
    names = list(MUSIC) + [f"band_{a}_normal" for a in ANIMAL_ORDER] + list(EFFECTS)
    at = 0.0
    for name in names:
        x, rate = read(OUT / f"{name}.wav")
        if rate != sr:
            x = resample_poly(x, sr, rate)
        if name in MUSIC:
            x = x[: int(6 * sr)] * env(int(6 * sr), 0.01, 0.5, sr)
        print(f"  {int(at // 60)}:{at % 60:04.1f}  {name}")
        pieces += [x, np.zeros(int(gap * sr))]
        at += (len(x) + len(pieces[-1])) / sr
    _encode(path, np.concatenate(pieces), sr)


def band_preview(path):
    """The whole band: the animals join one per loop at 100 beats a minute, as the app mixes them (volume 0.6 each)."""
    loops = [read(OUT / f"band_{a}_normal.wav")[0] for a in ANIMAL_ORDER]
    n = len(loops[0])
    out = np.zeros(n * (len(loops) + 1))
    for k, x in enumerate(loops):
        for rep in range(k, len(loops) + 1):
            out[rep * n:(rep + 1) * n] += 0.6 * x
    print(f"  band: peak {np.abs(out).max():.2f} with all ten (the engine clips at 1.0)")
    _encode(pathlib.Path(path), resample_poly(out, 22050, LOOP_SR), 22050)


def _encode(path, whole, sr):
    scratch = "/dev/shm" if os.path.isdir("/dev/shm") else tempfile.gettempdir()
    fd, wav = tempfile.mkstemp(suffix=".wav", dir=scratch)
    os.close(fd)
    try:
        write(wav, whole, min(0.98, np.abs(whole).max()), sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "aac", "-b:a", "96k", str(path)], check=True)
    finally:
        os.unlink(wav)
    print(f"  wrote {path}")


def main():
    args = sys.argv[1:]
    if args[:1] == ["band"]:
        band_preview(args[1])
        return
    only = args if args and args[0] != "preview" else None
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".gitkeep").unlink(missing_ok=True)
    print(f"band loops (16,000 Hz, {LOOP_BEATS} beats, one length per tempo), loudness {LOOP_LOUD:.0f} dB, peak at most {LOOP_PEAK}:")
    for a in ANIMAL_ORDER:
        for tname, bpm in TEMPOS.items():
            name = f"band_{a}_{tname}"
            if only and name not in only:
                continue
            x = highpass(band_loop(a, bpm), 40, LOOP_SR)
            data = write(OUT / f"{name}.wav", x, loop_level(x, LOOP_LOUD, LOOP_PEAK), LOOP_SR)
            assert len(data) == loop_samples(bpm)
            loop_report(name, data, LOOP_SR)
    print("music (16,000 Hz, loops):")
    for name, (make, want) in MUSIC.items():
        if only and name not in only:
            continue
        x = highpass(make(), 40, LOOP_SR)
        assert 18 <= len(x) / LOOP_SR <= 30, (name, len(x) / LOOP_SR)
        loop_report(name, write(OUT / f"{name}.wav", x, loop_level(x, want, MAX_PEAK), LOOP_SR), LOOP_SR)
    print(f"short sounds (22,050 Hz), loudness {TARGET:.0f} dB plus or minus, peaks at most {MAX_PEAK}:")
    for name, (make, offset, longest) in EFFECTS.items():
        if only and name not in only:
            continue
        x = tidy(phone_ready(make()))
        assert len(x) / SR <= longest, (name, len(x) / SR)
        data = write(OUT / f"{name}.wav", x, level(x, offset), SR)
        assert data[0] == 0 and data[-1] == 0, name
        report(name, data, SR, False, TARGET + offset)
    if only:
        return
    want = set(MUSIC) | set(EFFECTS) | set(band_names())
    names = {p.stem for p in OUT.glob("*.wav")}
    assert names == want, names ^ want
    assert {p.name for p in OUT.iterdir()} == {f"{n}.wav" for n in names}, "only the sounds belong in the folder"
    total = sum(p.stat().st_size for p in OUT.glob("*.wav"))
    print(f"{len(names)} sounds, {total:,} bytes ({total / 1024 / 1024:.2f} MiB) in {OUT}")
    assert total < LIMIT, f"the sounds must stay under {LIMIT:,} bytes"
    if len(args) == 2 and args[0] == "preview":
        preview(args[1])


if __name__ == "__main__":
    main()
