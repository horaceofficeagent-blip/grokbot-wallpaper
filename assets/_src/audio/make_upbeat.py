# Original upbeat loop (~120 bpm, C major pentatonic) — K-pop-inspired energy, not a cover.
# Usage: python3 make_upbeat.py <out_dir>  -> loop-raw.wav + ir.wav
import math, random, wave, array, os, sys

SR = 44100
TAU = 2 * math.pi
sin, exp, tanh = math.sin, math.exp, math.tanh
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
BARS = 16
CYCLE = BARS * BAR
OVERLAP = 2.0
N = int((3 * CYCLE + 4) * SR)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

L = array.array('f', bytes(4 * N))
R = array.array('f', bytes(4 * N))


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def put(t0, sig, gain=1.0, pan=0.0, sig_r=None):
    i0 = int(round(t0 * SR))
    gl = math.cos((pan + 1) * math.pi / 4) * gain * 1.4142
    gr = math.sin((pan + 1) * math.pi / 4) * gain * 1.4142
    r = sig_r if sig_r is not None else sig
    for k in range(max(0, -i0), min(len(sig), N - i0)):
        L[i0 + k] += sig[k] * gl
        R[i0 + k] += r[k] * gr


def norm(x):
    p = max(abs(v) for v in x) or 1.0
    return [v / p for v in x]


TB = 2048
SAW = [sum(sin(TAU * h * i / TB) / h for h in range(1, 16)) for i in range(TB)]
_m = max(abs(v) for v in SAW)
SAW = [v / _m for v in SAW]
SQR = [1.0 if (i % TB) < TB // 2 else -1.0 for i in range(TB)]


def kick():
    out, ph = [], 0.0
    for k in range(int(0.28 * SR)):
        t = k / SR
        ph += TAU * (52 + 120 * exp(-t * 35)) / SR
        out.append(tanh(1.6 * exp(-t * 12) * sin(ph)))
    return norm(out)


def clap():
    rng = random.Random(11)
    out, y = [], 0.0
    for k in range(int(0.22 * SR)):
        t = k / SR
        x = rng.random() * 2 - 1
        y += 0.55 * (x - y)
        burst = exp(-max(0, t - 0.012) * 55) if t > 0.012 else exp(-t * 180)
        out.append((x - 0.6 * y) * burst + 0.25 * sin(TAU * 980 * t) * exp(-t * 70))
    return norm(out)


def hat(open_=False):
    rng = random.Random(5 if open_ else 7)
    n = int((0.18 if open_ else 0.06) * SR)
    out, lp = [], 0.0
    for k in range(n):
        t = k / SR
        x = rng.random() * 2 - 1
        lp += 0.35 * (x - lp)
        a = (1 - exp(-t * 400)) * exp(-t * (18 if open_ else 70))
        out.append((x - lp) * a)
    return norm(out)


def bass(m, dur):
    w = TAU * hz(m) / SR
    n = int((dur + 0.08) * SR)
    out = [0.0] * n
    for k in range(n):
        t = k / SR
        a = (1 - exp(-t * 220)) * (0.75 + 0.25 * exp(-t * 8))
        if t > dur:
            a *= max(0.0, 1 - (t - dur) / 0.08)
        out[k] = a * tanh(1.4 * (sin(w * k) + 0.35 * sin(2 * w * k)))
    return out


def stab(notes, dur):
    n = int((dur + 0.25) * SR)
    a = [0.0] * n
    for m in notes:
        f, ph = hz(m), random.Random(m).random() * TB
        inc = f * TB / SR
        for k in range(n):
            t = k / SR
            e = (1 - exp(-t * 90)) * exp(-t * 5.5)
            if t > dur:
                e *= max(0.0, 1 - (t - dur) / 0.2)
            a[k] += SAW[int(ph) & 2047] * e
            ph += inc
    return norm(a)


def lead(m, dur):
    w = TAU * hz(m) / SR
    n = int((dur + 0.15) * SR)
    out = [0.0] * n
    for k in range(n):
        t = k / SR
        a = (1 - exp(-t * 250)) * exp(-t * 3.2)
        if t > dur:
            a *= max(0.0, 1 - (t - dur) / 0.12)
        vib = 1 + 0.004 * sin(TAU * 5.5 * t)
        out[k] = a * (0.7 * sin(w * k * vib) + 0.3 * SQR[int((w * k * TB / TAU) % TB)])
    return out


KICK, CLAP, HAT, OHAT = kick(), clap(), hat(False), hat(True)

# Chord colours in C: bright pop progression
PROG = [
    (36, [60, 64, 67, 72]),  # C
    (41, [60, 65, 69, 72]),  # F
    (33, [57, 60, 64, 69]),  # Am
    (43, [59, 62, 67, 71]),  # G
]
PROG = PROG * 4  # 16 bars

# Catchy original hook (scale degrees in C penta: C D E G A)
HOOK = [72, 74, 76, 79, 76, 74, 72, 76, 79, 81, 79, 76, 74, 72, 67, 72]

for cycle in range(3):
    for b, (root, voicing) in enumerate(PROG):
        t = cycle * CYCLE + b * BAR
        # four-on-floor + clap on 2/4
        for s in range(4):
            put(t + s * BEAT, KICK, 0.42 if s == 0 else 0.34)
        put(t + BEAT, CLAP, 0.38, 0.05)
        put(t + 3 * BEAT, CLAP, 0.36, -0.05)
        for s in range(8):
            put(t + s * BEAT / 2, HAT, 0.08 if s % 2 else 0.05, 0.4)
        if b % 2 == 1:
            put(t + 1.5 * BEAT, OHAT, 0.1, -0.35)
        # bass pulse
        put(t, bass(root, 0.85 * BEAT), 0.32)
        put(t + BEAT, bass(root, 0.4 * BEAT), 0.22)
        put(t + 2 * BEAT, bass(root, 0.85 * BEAT), 0.28)
        put(t + 3 * BEAT, bass(root + 12, 0.35 * BEAT), 0.16)
        # chord stabs on 1 and the "and" of 2
        put(t, stab(voicing, 0.35 * BEAT), 0.16, -0.2)
        put(t + 1.5 * BEAT, stab(voicing, 0.45 * BEAT), 0.13, 0.15)
        # lead hook — one note per half-bar through the cycle
        hi = HOOK[b % len(HOOK)]
        put(t + 0.05, lead(hi, 0.7 * BEAT), 0.14, 0.25)
        if b % 4 == 2:
            put(t + 2.05 * BEAT, lead(hi + 5 if hi < 81 else hi - 5, 0.55 * BEAT), 0.11, -0.2)


def write(path, a, b, target=0.9):
    p = max(max(abs(v) for v in a), max(abs(v) for v in b)) or 1.0
    k = target / p
    data = array.array('h', bytes(4 * len(a)))
    for i in range(len(a)):
        data[2 * i] = int(max(-1, min(1, a[i] * k)) * 32767)
        data[2 * i + 1] = int(max(-1, min(1, b[i] * k)) * 32767)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())


def make_ir(length=2.0, rt60=1.4, pre=0.01):
    r2 = random.Random(21)
    n = int(length * SR)
    a, b = [0.0] * n, [0.0] * n
    yl = yr = 0.0
    for k in range(int(pre * SR), n):
        t = k / SR - pre
        g = exp(-6.91 * t / rt60)
        c = 1 - exp(-TAU * (800 + 9000 * exp(-t * 2.2)) / SR)
        yl += c * ((r2.random() * 2 - 1) - yl)
        yr += c * ((r2.random() * 2 - 1) - yr)
        a[k], b[k] = g * yl, g * yr
    return a, b


write(os.path.join(OUT, 'loop-raw.wav'), L, R, 0.72)
write(os.path.join(OUT, 'ir.wav'), *make_ir())
print(f'upbeat cycle {CYCLE:.4f} s @ {BPM} bpm, overlap {OVERLAP} s')
