# Original soft lo-fi / chill loop (~90 bpm, C major pentatonic).
# Usage: python3 make_chill.py <out_dir>  -> loop-raw.wav + ir.wav
import math, random, wave, array, os, sys

SR = 44100
TAU = 2 * math.pi
sin, exp, tanh = math.sin, math.exp, math.tanh
BPM = 90
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
SAW = [sum(sin(TAU * h * i / TB) / h for h in range(1, 12)) for i in range(TB)]
_m = max(abs(v) for v in SAW)
SAW = [v / _m for v in SAW]


def pad(notes, dur, att=0.8, rel=1.2, cutoff=700):
    n = int((dur + rel) * SR)
    a, b = [0.0] * n, [0.0] * n
    rng = random.Random(hash(tuple(notes)) & 0xffff)
    for m in notes:
        f = hz(m)
        for det, main, other in ((-0.004, a, b), (0.004, b, a)):
            inc, ph = f * (1 + det) * TB / SR, rng.random() * TB
            for k in range(n):
                v = SAW[int(ph) & 2047]
                ph += inc
                main[k] += v
                other[k] += 0.4 * v
    c = 1 - exp(-TAU * cutoff / SR)
    yl = yr = 0.0
    for k in range(n):
        t = k / SR
        e = 0.5 - 0.5 * math.cos(math.pi * t / att) if t < att else (
            0.5 + 0.5 * math.cos(math.pi * min(1.0, (t - dur) / rel)) if t > dur else 1.0)
        yl += c * (a[k] - yl); yr += c * (b[k] - yr)
        a[k], b[k] = yl * e, yr * e
    return a, b


def soft_kick():
    out, ph = [], 0.0
    for k in range(int(0.5 * SR)):
        t = k / SR
        ph += TAU * (40 + 60 * exp(-t * 18)) / SR
        out.append(tanh(1.1 * exp(-t * 5) * sin(ph)))
    return norm(out)


def soft_snare():
    rng = random.Random(2)
    out, y = [], 0.0
    for k in range(int(0.3 * SR)):
        t = k / SR
        x = rng.random() * 2 - 1
        y += 0.4 * (x - y)
        out.append((y + 0.2 * sin(TAU * 180 * t)) * exp(-t * 10))
    return norm(out)


def keys(m, dur):
    w = TAU * hz(m) / SR
    n = int((dur + 0.9) * SR)
    out = [0.0] * n
    for k in range(n):
        t = k / SR
        a = exp(-t * 1.1) * (1 - exp(-t * 120))
        if t > dur:
            a *= exp(-(t - dur) * 4)
        out[k] = a * (sin(w * k) + 0.15 * sin(2 * w * k))
    return out


def vinyl(n):
    rng = random.Random(42)
    out, y = [0.0] * n, 0.0
    for k in range(n):
        x = rng.random() * 2 - 1
        y += 0.02 * (x - y)
        out[k] = y * 0.015
        if rng.random() < 0.0004:
            out[k] += (rng.random() - 0.5) * 0.08
    return out


KICK, SNARE = soft_kick(), soft_snare()
PROG = [
    (36, [60, 64, 67, 71]),
    (41, [60, 65, 69, 72]),
    (33, [57, 60, 64, 67]),
    (38, [57, 62, 65, 69]),
] * 4
MELODY = [76, None, 79, 76, 74, None, 72, 74, 76, 79, None, 81, 79, 76, 74, 72]

for cycle in range(3):
    crackle = vinyl(int(CYCLE * SR))
    put(cycle * CYCLE, crackle, 1.0, 0)
    for b, (root, voicing) in enumerate(PROG):
        t = cycle * CYCLE + b * BAR
        pa, pb = pad(voicing, BAR * 0.95)
        put(t, pa, 0.022, 0, pb)
        put(t, KICK, 0.28)
        put(t + 2 * BEAT, KICK, 0.18)
        put(t + 1.5 * BEAT, SNARE, 0.12, 0.1)
        put(t, keys(root + 12, 2.0 * BEAT), 0.08, -0.25)
        for i, m in enumerate(voicing[:3]):
            put(t + 0.02 * i, keys(m, 1.6 * BEAT), 0.05, -0.2 + 0.15 * i)
        note = MELODY[b % len(MELODY)]
        if note is not None:
            put(t + 0.5 * BEAT, keys(note, 1.2 * BEAT), 0.07, 0.3)


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


def make_ir(length=2.8, rt60=2.2, pre=0.02):
    r2 = random.Random(3)
    n = int(length * SR)
    a, b = [0.0] * n, [0.0] * n
    yl = yr = 0.0
    for k in range(int(pre * SR), n):
        t = k / SR - pre
        g = exp(-6.91 * t / rt60)
        c = 1 - exp(-TAU * (400 + 5000 * exp(-t * 1.5)) / SR)
        yl += c * ((r2.random() * 2 - 1) - yl)
        yr += c * ((r2.random() * 2 - 1) - yr)
        a[k], b[k] = g * yl, g * yr
    return a, b


write(os.path.join(OUT, 'loop-raw.wav'), L, R, 0.55)
write(os.path.join(OUT, 'ir.wav'), *make_ir())
print(f'chill cycle {CYCLE:.4f} s @ {BPM} bpm, overlap {OVERLAP} s')
