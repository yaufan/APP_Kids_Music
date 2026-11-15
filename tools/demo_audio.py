#!/usr/bin/env python3
"""Puts the music, the band and the sounds under the demo video.

test/demo/demo_video_test.dart writes, next to the silent video, what the app asked the sound engine
for, frame by frame (app/build/demo/sounds.txt):

    <frame> sfx <name>                  a short sound
    <frame> music <name>|-              the music that plays from now (looping), or none
    <frame> bandstart <tempo> <a,b,..>  the band starts: every loop at one moment, these animals heard
    <frame> band <tempo> <a,b,..>       from the next bar line on, only these animals are heard
    <frame> bandstop
    <frame> song <name> <ms>            a note of a song, <ms> after the song starts
    <frame> songstop                    the notes of the song not yet played are cancelled

This mixes the same files from app/assets/sounds the way the app's engine does (the band's loops
all aligned to the moment it started, joins and leaves on the next bar line) and writes
app/build/demo/demo.mp4.

    python3 tools/demo_audio.py
"""
import pathlib
import subprocess
import sys
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEMO = ROOT / "app/build/demo"
SOUNDS = ROOT / "app/assets/sounds"
RATE = 22050
MUSIC_GAIN, SFX_GAIN, BAND_GAIN = 0.45, 0.85, 0.7
FADE = 0.3            # seconds, when the music changes
BPM = {"slow": 80, "normal": 100, "fast": 120}
START_LEAD = 0.12     # the engine starts the band this long after it is asked
SONG_LEAD = 0.08


def load(name, cache={}):
    if name in cache:
        return cache[name]
    with wave.open(str(SOUNDS / f"{name}.wav")) as w:
        rate, n = w.getframerate(), w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
    if rate != RATE:
        t = np.arange(int(len(data) * RATE / rate)) * rate / RATE
        data = np.interp(t, np.arange(len(data)), data)
    cache[name] = data
    return data


def add(track, at, sig, gain=1.0):
    if at >= len(track):
        return
    end = min(len(track), at + len(sig))
    track[at:end] += gain * sig[: end - at]


def main():
    lines = [l for l in (DEMO / "sounds.txt").read_text().split("\n") if l.strip()]
    fps = int(lines[0].split()[1])
    frames = int(lines[1].split()[1])
    total = int(frames / fps * RATE) + RATE
    music = np.zeros(total)
    sfx = np.zeros(total)
    band = np.zeros(total)
    changes = []
    song = []           # (sample, name)
    # the band as segments: (from, to, tempo, t0, animals)
    seg = None
    segments = []
    for line in lines[2:]:
        parts = line.split()
        frame, kind, args = int(parts[0]), parts[1], parts[2:]
        at = int(frame / fps * RATE)
        if kind == "sfx":
            add(sfx, at, load(args[0]))
        elif kind == "music":
            changes.append((at, None if args[0] == "-" else args[0]))
        elif kind == "song":
            song.append((at + int((SONG_LEAD + int(args[1]) / 1000) * RATE), args[0]))
        elif kind == "songstop":
            song = [(s, n) for s, n in song if s < at]
        elif kind in ("bandstart", "band", "bandstop"):
            if kind == "bandstart":
                if seg:
                    segments.append((seg[0], at, *seg[1:]))
                t0 = at + int(START_LEAD * RATE)
                animals = args[1].split(",") if len(args) > 1 and args[1] else []
                seg = (t0, args[0], t0, animals)
            elif kind == "band" and seg:
                bar = int(4 * 60 / BPM[seg[1]] * RATE)
                nxt = seg[2] + -(-(at - seg[2]) // bar) * bar
                segments.append((seg[0], nxt, *seg[1:]))
                animals = args[1].split(",") if len(args) > 1 and args[1] else []
                seg = (nxt, seg[1], seg[2], animals)
            elif kind == "bandstop" and seg:
                segments.append((seg[0], at, *seg[1:]))
                seg = None
    if seg:
        segments.append((seg[0], total, *seg[1:]))
    for s, n in song:
        add(sfx, s, load(n))
    for start, end, tempo, t0, animals in segments:
        if end <= start:
            continue
        idx = np.arange(start, end)
        for a in animals:
            loop = load(f"band_{a}_{tempo}")
            band[start:end] += loop[(idx - t0) % len(loop)]
    changes.append((total, None))
    fade = int(FADE * RATE)
    for (start, name), (end, _) in zip(changes, changes[1:]):
        if name is None or end <= start:
            continue
        loop = load(name)
        n = end - start
        piece = np.tile(loop, n // len(loop) + 1)[:n].copy()
        ramp = min(fade, n // 2)
        piece[:ramp] *= np.linspace(0, 1, ramp)
        piece[n - ramp:] *= np.linspace(1, 0, ramp)
        music[start:end] += piece
    mix = music * MUSIC_GAIN + sfx * SFX_GAIN + band * BAND_GAIN
    peak = np.abs(mix).max()
    if peak > 0.95:
        mix *= 0.95 / peak
    pcm = (mix * 32767).astype(np.int16)
    out = DEMO / "demo_audio.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(DEMO / "demo_silent.mp4"), "-i", str(out),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(DEMO / "demo.mp4")],
        check=True,
    )
    out.unlink()
    print(f"{DEMO / 'demo.mp4'}: {frames / fps:.1f} s, peak {peak:.2f}, {len(segments)} band parts")


if __name__ == "__main__":
    sys.exit(main())
