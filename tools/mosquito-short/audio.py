"""audio — the 25-second soundtrack for "Mosquito: An Overreaction".

Builds the full mix from synthesis (no external assets except the narrator's VO,
which is decoded with the bundled ffmpeg):

  * deadpan narrator: five VO lines placed on the beat
  * comedy score: sneaky pizzicato plucks, walking bass, wood ticks, a heartbeat
    that accelerates into the orbital strike, then a nervous quiet for the punchline
  * SFX: snoring, a mosquito buzz that will not die, whiffs, slaps, furniture
    demolition, bazooka thump, flamethrower roar, button click, laser charge,
    city-erasing explosion and its long crater rumble

Usage:  python3 audio.py  ->  audio/mix.wav (48 kHz stereo)
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
import wave

import numpy as np

SR = 48000
DUR = 25.0
N = int(SR * DUR)
rng = np.random.default_rng(20261016)

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")


def t_of(i):
    return i / SR


def idx(t):
    return int(round(t * SR))


# --------------------------------------------------------------- helpers ----
def add(buf, sig, t0, gain=1.0):
    i0 = idx(t0)
    if i0 >= len(buf):
        return
    n = min(len(sig), len(buf) - i0)
    if n <= 0:
        return
    buf[i0:i0 + n] += sig[:n] * gain


def env(n, a=0.005, d=0.05, s=0.0, r=0.1, sustain=0.0):
    """simple ADSR over n samples"""
    e = np.zeros(n, dtype=np.float32)
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = max(1, min(ai, n))
    e[:ai] = np.linspace(0, 1, ai)
    di = max(1, min(di, n - ai))
    e[ai:ai + di] = np.linspace(1, max(sustain, 1e-4), di)
    tail = n - ai - di
    if tail > 0:
        e[ai + di:] = max(sustain, 1e-4)
    if sustain > 0 and ri > 0:
        ri = min(ri, n)
        e[n - ri:] *= np.linspace(1, 0, ri)
    else:
        e[ai + di:] = np.linspace(max(sustain, 1e-4), 0, tail) if tail > 0 else e[ai + di:]
    return e


def noise(n, lp=0.1, hp=0.0005):
    x = rng.normal(0, 1, n).astype(np.float32)
    # one-pole low pass
    a = math.exp(-2 * math.pi * lp)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(n):
        acc = a * acc + (1 - a) * x[i]
        y[i] = acc
    if hp > 0:
        b = math.exp(-2 * math.pi * hp)
        z = np.empty_like(y)
        acc2 = 0.0
        for i in range(n):
            acc2 = b * acc2 + (1 - b) * y[i]
            z[i] = y[i] - acc2
        y = z
    m = np.max(np.abs(y)) or 1.0
    return y / m


def sine(f, n, ph=0.0):
    t = np.arange(n, dtype=np.float32) / SR
    return np.sin(2 * np.pi * f * t + ph).astype(np.float32)


def pluck(freq, dur, bright=0.5, decay=5.0):
    """Karplus-Strong: sneaky pizzicato string"""
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    buf = rng.normal(0, 1, p).astype(np.float32)
    buf = np.convolve(buf, np.array([bright, 1 - bright], dtype=np.float32), mode="same")
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * math.exp(-decay / SR * 40)
    return out * np.exp(-np.arange(n) / SR * 3.0).astype(np.float32)


def kick(dur=0.32, f0=110, f1=44, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 24)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 8) * gain).astype(np.float32)


def wood(dur=0.09, f=780, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.7 * t))
            * np.exp(-t * 42) * gain).astype(np.float32)


def swoosh(dur=0.26, f_lo=200, f_hi=2600, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n).astype(np.float32)
    f = f_lo + (f_hi - f_lo) * (t / dur) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    bp = np.sin(ph) * x
    return (bp * np.exp(-((t - dur * 0.55) / (dur * 0.4)) ** 2) * gain).astype(np.float32)


def crash(dur=1.5, gain=1.0, seed=None):
    """furniture demolition: broadband impact + wood cracks + rattling debris"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t * 7.5)
    body = np.convolve(body, np.ones(9, dtype=np.float32) / 9, mode="same")
    out = body
    r = np.random.default_rng(seed or 1)
    for i in range(7):
        tt = r.uniform(0.0, dur * 0.45)
        f = r.uniform(320, 1500)
        out[idx(tt) - idx(0):idx(tt) + len(wood(0.14, f))] += wood(0.14, f, r.uniform(0.5, 1.0)) if \
            idx(tt) + len(wood(0.14, f)) <= n else 0
    return (out * gain).astype(np.float32)


def boom(dur=3.2, gain=1.0):
    """the orbital strike"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 66 * np.exp(-t * 1.35) + 22
    ph = 2 * np.pi * np.cumsum(f) / SR
    low = np.sin(ph) * np.exp(-t * 1.5)
    rumble = np.convolve(rng.normal(0, 1, n).astype(np.float32),
                         np.ones(280, dtype=np.float32) / 280, mode="same") * np.exp(-t * 0.75)
    crack = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t * 16)
    return (low * 1.0 + rumble * 1.5 + crack * 0.7) * gain


def buzz(dur, f0=520.0, gain=1.0, flutter=7.0, seed=4):
    """the mosquito: two detuned saws, wobbling, with a fast amplitude flutter"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    vib = 1 + 0.03 * np.sin(2 * np.pi * 5.5 * t) + 0.012 * np.sin(2 * np.pi * 41 * t + 1.0)
    out = np.zeros(n, dtype=np.float32)
    for k, (f, a) in enumerate(((f0, 0.6), (f0 * 1.26, 0.45), (f0 * 2.02, 0.22), (f0 * 3.7, 0.09))):
        ph = 2 * np.pi * np.cumsum(f * vib * (1 + 0.002 * r.normal(0, 1, n))) / SR
        saw = 2 * ((ph / (2 * np.pi)) % 1.0) - 1.0
        out += saw * a
    out *= 0.6 + 0.4 * np.sin(2 * np.pi * flutter * t + 2.0) ** 2
    edge = np.minimum(1, np.minimum(t / 0.05, (dur - t) / 0.06))
    return (out * edge * 0.5 * gain).astype(np.float32)


def band_noise(dur, lo, hi, gain=1.0, wobble=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n).astype(np.float32)
    f = (lo + hi) / 2 * (1 + wobble * np.sin(2 * np.pi * 6.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) * x)
    return (y * gain).astype(np.float32)


def snore(dur=0.85, gain=1.0, seed=2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n).astype(np.float32)
    f = 160 - 70 * (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = x * (0.4 + 0.6 * np.sin(ph))
    e = np.exp(-((t - dur * 0.42) / (dur * 0.34)) ** 2)
    return (y * e * gain * 0.7).astype(np.float32)


# ---------------------------------------------------------------- decode ----
def load_mp3(path, speed=1.0):
    """decode a file to mono float32 at SR, time-compressed with ffmpeg atempo"""
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, "-v", "error", "-i", path]
    if abs(speed - 1.0) > 1e-3:
        cmd += ["-filter:a", f"atempo={speed:.3f}"]
    cmd += ["-f", "s16le", "-acodec", "pcm_s16le", "-ar", str(SR), "-ac", "1", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def main():
    os.makedirs(AUDIO, exist_ok=True)
    L = np.zeros(N, dtype=np.float32)
    R = np.zeros(N, dtype=np.float32)

    def st(sig, t0, gain=1.0, pan=0.0):
        g = 0.5 * (1 - pan)
        add(L, sig, t0, gain * (1 - max(0.0, pan)))
        add(R, sig, t0, gain * (1 + min(0.0, pan)))

    # ===================== 1. score: sneaky pizzicato ======================
    # A minor pizzicato figure; sparse in the hook, frantic in the escalation.
    A2, C3, E3, A3, G3, F3, D3, E4, A4 = 110.0, 130.81, 164.81, 220.0, 196.0, 174.61, 146.83, 329.63, 440.0
    beat = 0.30                                   # 200 bpm eighth-note pulse
    pattern = [A3, E4, C3, E3, A3, G3, E4, D3]
    t = 0.30
    k = 0
    while t < 19.2:
        # density: sparse early, dense in the escalation, frantic before the strike
        if t < 3.2:
            play = (k % 8) in (0, 3, 6)
            dec = 3.4
        elif t < 10.7:
            play = True
            dec = 3.6
        elif t < 17.4:
            play = (k % 8) in (0, 1, 3, 4, 6)
            dec = 4.2
        else:
            play = (k % 4) in (0, 2)
            dec = 5.5
        if play:
            f = pattern[k % len(pattern)] * (1.0 if t < 17.4 else (1 + 0.5 * ((k // 4) % 2)))
            p = pluck(f, 0.55, bright=0.6, decay=dec) * 0.22
            st(p, t, 1.0, pan=0.25 * (1 if k % 2 else -1))
        # walking bass on the downbeat
        if k % 4 == 0:
            st(pluck([A2, F3 / 2, G3 / 2, D3 / 1.0][(k // 4) % 4], 0.7, bright=0.35, decay=2.2) * 0.30,
               t, 1.0, pan=-0.18)
        # wood ticks
        if 3.2 < t and (k % 2 == 0):
            st(wood(0.05, 1250 + 220 * (k % 3), 0.10), t, 1.0, pan=0.4)
        t += beat
        k += 1

    # heartbeat that accelerates into the strike
    hb = 10.8
    gap = 0.62
    while hb < 18.2:
        st(kick(0.30, 96, 40, 0.55), hb, 1.0)
        st(kick(0.24, 88, 36, 0.34), hb + gap * 0.42, 1.0)
        gap = max(0.20, gap * 0.93)
        hb += gap
    # rising tension sweep before the orbital strike
    n = int((18.2 - 16.3) * SR)
    tt = np.arange(n) / SR
    sweep = (np.sin(2 * np.pi * np.cumsum(180 + 1500 * (tt / tt[-1]) ** 2) / SR)
             * np.exp(-np.maximum(0, tt - tt[-1] * 0.9) * 30) * 0.30)
    sweep *= np.linspace(0, 1, n) ** 0.8
    st(sweep.astype(np.float32), 16.3, 1.0)

    # nervous quiet for the crater, then a queasy high shimmer
    for i, tt2 in enumerate(np.arange(19.8, 22.4, 0.42)):
        st(pluck([A3, C3, E3, A2][i % 4], 0.8, bright=0.4, decay=1.8) * 0.12, float(tt2), 1.0,
           pan=0.2 * (1 if i % 2 else -1))
    sh = np.arange(int(3.0 * SR)) / SR
    st((np.sin(2 * np.pi * 1560 * sh) * 0.02 * (1 + np.sin(2 * np.pi * 0.6 * sh))).astype(np.float32),
       21.4, 1.0)
    st(pluck(A2, 3.0, bright=0.3, decay=0.7) * 0.16, 21.9, 1.0)

    # ============================ 2. SFX ===================================
    # snoring in the hook
    st(snore(0.9, 0.5), 0.55)
    st(snore(0.9, 0.42), 1.45)
    # the buzz arrives and does not leave
    st(buzz(1.75, 470, 0.30, 6.0, 4), 0.45)
    st(buzz(5.6, 520, 0.22, 7.0, 5), 2.30)          # rage onslaught
    st(buzz(7.6, 505, 0.16, 6.0, 6), 3.30)
    st(buzz(2.4, 480, 0.13, 6.5, 7), 12.90)
    # the whiff of a slap that hits nothing, and the slap that hits him
    st(swoosh(0.30, 160, 2100, 0.32), 1.06)
    st(kick(0.22, 180, 60, 0.5), 1.14)
    st(band_noise(0.14, 900, 2600, 0.30), 1.14)
    st(swoosh(0.36, 120, 1800, 0.36), 1.72)
    # the flyswatter: whiffs, demolition, the mosquito never being hit
    for (tt3, g) in ((2.28, 0.30), (3.02, 0.36), (3.66, 0.40), (4.62, 0.46), (7.06, 0.30)):
        st(swoosh(0.30, 90, 1400, g), tt3)
    st(kick(0.42, 130, 34, 0.85), 2.62, 1.0)        # slamming his own face
    st(band_noise(0.20, 700, 2200, 0.20), 2.62)
    for (tt4, seed) in ((3.02, 11), (3.66, 12), (4.62, 13)):   # furniture bites it
        st(crash(1.6, 0.85, seed), tt4, 1.0, pan=0.25 if seed % 2 else -0.25)
    st(wood(0.12, 520, 0.30), 4.66)
    st(crash(1.2, 0.4, 21), 7.1, 1.0, pan=0.2)
    # bazooka
    st(band_noise(0.5, 300, 1200, 0.22), 11.95)
    st(kick(0.5, 150, 42, 0.9), 12.5)
    st(band_noise(0.7, 200, 1400, 0.42), 12.5)
    st(band_noise(0.5, 240, 900, 0.18), 13.05)
    # flamethrower roar
    roar = band_noise(1.45, 200, 1500, 0.5, wobble=0.35)
    st(roar, 14.25, 1.0)
    st(band_noise(1.2, 120, 600, 0.22), 14.35, 1.0)
    st(wood(0.08, 1500, 0.22), 14.2)
    # emergency console: cover flips, button clunks, charge rises
    st(wood(0.10, 980, 0.30), 16.60)
    st(wood(0.09, 620, 0.36), 16.94)
    st(kick(0.3, 190, 70, 0.4), 16.96)
    chg = np.arange(int(1.05 * SR)) / SR
    st((np.sin(2 * np.pi * np.cumsum(300 + 900 * (chg / chg[-1]) ** 2) / SR) * 0.22
        * (0.4 + 0.6 * np.sin(2 * np.pi * 15 * chg) ** 2)).astype(np.float32), 16.95, 1.0)
    # orbital laser: descending shriek, then the world ends
    z = np.arange(int(0.9 * SR)) / SR
    st((np.sin(2 * np.pi * np.cumsum(2600 - 1500 * (z / z[-1])) / SR) * 0.30
        * (1 - 0.5 * (z / z[-1]))).astype(np.float32), 17.42, 1.0)
    st(band_noise(0.9, 800, 3000, 0.34), 17.42)
    st(band_noise(0.55, 300, 1200, 0.30), 17.9)
    st(boom(3.6, 1.15), 18.22, 1.0, pan=0.0)
    st(np.convolve(rng.normal(0, 1, int(4.6 * SR)).astype(np.float32),
                   np.ones(420, dtype=np.float32) / 420, mode="same") * 0.34, 18.35, 1.0)
    st(band_noise(1.4, 150, 700, 0.20), 18.5)
    # debris landing + the very long crater quiet
    for tt5 in (20.3, 20.65, 21.05):
        r2 = np.random.default_rng(int(tt5 * 10))
        st(wood(r2.uniform(0.06, 0.12), r2.uniform(500, 1200), 0.16), tt5, 1.0,
           pan=float(r2.uniform(-0.5, 0.5)))
    # punchline: buzz right at the lens, then the faint
    st(buzz(2.5, 560, 0.34, 8.0, 9), 22.35)
    st(buzz(0.9, 620, 0.38, 9.0, 10), 22.35, pan=0.0)
    st(swoosh(0.22, 200, 2400, 0.22), 23.9)
    st(kick(0.6, 120, 30, 0.7), 24.42)
    st(crash(1.4, 0.45, 33), 24.44, 1.0)
    st(band_noise(0.5, 200, 800, 0.16), 24.42)

    # ==================== 3. narrator (deadpan, dry) =======================
    vo = [("vo1.mp3", 0.38, 1.00, 1.22), ("vo2.mp3", 3.66, 0.98, 1.26), ("vo3.mp3", 8.72, 0.98, 1.26),
          ("vo4.mp3", 13.28, 1.00, 1.26), ("vo5.mp3", 20.30, 1.02, 1.24)]
    for name, t0, g, spd in vo:
        p = os.path.join(AUDIO, name)
        if not os.path.exists(p):
            print("missing", p)
            continue
        y = load_mp3(p, spd)
        # gentle trim of leading/trailing silence
        thr = 0.012
        nz = np.nonzero(np.abs(y) > thr)[0]
        if len(nz):
            y = y[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.05 * SR)]
        y = y * g
        add(L, y, t0, 0.95)
        add(R, y, t0, 0.95)
        print(f"{name}: {len(y)/SR:.2f}s -> starts {t0:.2f}, ends {t0+len(y)/SR:.2f}")

    # ========================= 4. master chain =============================
    mix = np.stack([L, R])
    # soft clip + gentle limiter
    mix = np.tanh(mix * 1.15) * 0.92
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = mix / peak * 0.94
    # tiny fade in/out
    f = int(0.05 * SR)
    mix[:, :f] *= np.linspace(0, 1, f)
    mix[:, -int(0.35 * SR):] *= np.linspace(1, 0, int(0.35 * SR))

    out = os.path.join(AUDIO, "mix.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype("<i2").tobytes())
    print("wrote", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
