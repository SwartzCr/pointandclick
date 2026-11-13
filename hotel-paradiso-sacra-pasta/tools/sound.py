"""Every sound effect and both pieces of music, synthesised with numpy and
written as 16-bit mono WAV files (22050 Hz)."""
import io
import math
import os
import wave
import numpy as np
from scipy.signal import lfilter

SR = 22050
rng = np.random.default_rng(714)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, d=0.1, s=0.0, r=0.05, dur=None):
    """ADSR-ish envelope of n samples (s = sustain level)."""
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    e = np.full(n, s, dtype=np.float64)
    a_n = min(a_n, n)
    e[:a_n] = np.linspace(0, 1, a_n, endpoint=False)
    d_end = min(n, a_n + d_n)
    e[a_n:d_end] = np.linspace(1, s, d_end - a_n, endpoint=False)
    if r_n and n > r_n:
        e[-r_n:] *= np.linspace(1, 0, r_n)
    return e


def decay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lp_fast(x, cutoff):
    """One-pole low-pass via cumulative trick (vectorised in chunks)."""
    a = math.exp(-2 * math.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


def tone(freq, dur, shape='sine', phase=0.0):
    t = t_(dur)
    if callable(freq):
        ph = 2 * np.pi * np.cumsum(freq(t)) / SR
    else:
        ph = 2 * np.pi * freq * t
    ph += phase
    if shape == 'sine':
        return np.sin(ph)
    if shape == 'square':
        return np.sign(np.sin(ph))
    if shape == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    if shape == 'tri':
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1
    raise ValueError(shape)


def pluck(freq, dur, bright=0.5):
    """Karplus-Strong plucked string; `bright` keeps more of the high end."""
    n = int(dur * SR)
    period = max(2, int(round(SR / freq)))
    buf = rng.uniform(-1, 1, period)
    out = np.empty(n)
    keep = 0.5 + bright * 0.45
    for i in range(n):
        j = i % period
        v = buf[j]
        out[i] = v
        buf[j] = 0.996 * (keep * v + (1 - keep) * buf[(j + 1) % period])
    return out


def mix(*parts, at=None, length=None):
    """parts: list of (offset_seconds, signal)."""
    end = max(int(o * SR) + len(sgl) for o, sgl in parts)
    if length:
        end = max(end, int(length * SR))
    out = np.zeros(end)
    for o, sgl in parts:
        i = int(o * SR)
        out[i:i + len(sgl)] += sgl
    return out


def modal(freqs, dur, tau=0.15, amp=None):
    """A struck object: a few decaying resonances."""
    n = int(dur * SR)
    out = np.zeros(n)
    amp = amp or [1.0 / (i + 1) for i in range(len(freqs))]
    for f, a in zip(freqs, amp):
        out += a * np.sin(2 * np.pi * f * t_(dur)) * decay(n, tau * (1.2 - 0.1 * freqs.index(f)))
    return out


def wav_bytes(x, vol=0.8):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1.0
    x = np.clip(x / peak * vol, -1, 1)
    pcm = (x * 32767).astype('<i2')
    b = io.BytesIO()
    with wave.open(b, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return b.getvalue()


# ------------------------------------------------------------------ effects
def creak(dur=0.6, f0=180, f1=120):
    n = int(dur * SR)
    f = lambda t: f0 + (f1 - f0) * (t / dur) + 20 * np.sin(t * 60)
    s = tone(f, dur, 'saw') * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * t_(dur))))
    return s * env(n, 0.02, dur * 0.6, 0.4, 0.1) * 0.6


def thunk(f=110, dur=0.25):
    n = int(dur * SR)
    return (modal([f, f * 2.3, f * 3.9], dur, 0.05) + noise(dur) * decay(n, 0.01) * 0.6)


def sfx_wardrobe_open():
    return mix((0, creak(0.7)), (0.62, thunk(140, 0.2) * 0.5))


def sfx_wardrobe_close():
    return mix((0, creak(0.35, 140, 200)), (0.3, thunk(90, 0.3)))


def sfx_clack():
    return modal([620, 1340, 2280], 0.18, 0.03) + noise(0.18) * decay(int(0.18 * SR), 0.004)


def sfx_ratchet():
    parts = [(i * 0.045, modal([1800, 3100], 0.04, 0.006) + noise(0.04) * decay(int(0.04 * SR), 0.002)) for i in range(6)]
    return mix(*parts)


def sfx_reset():
    return mix((0, thunk(80, 0.35)), (0.05, thunk(70, 0.35) * 0.6), (0.1, sfx_ratchet() * 0.4))


def sfx_drawer():
    n = int(0.45 * SR)
    rub = lp_fast(noise(0.45), 900) * env(n, 0.03, 0.3, 0.6, 0.1)
    return mix((0, rub), (0.4, thunk(160, 0.2) * 0.6))


def sfx_chime():
    notes = [784, 988, 1175, 1568]
    return mix(*[(i * 0.11, modal([f, f * 2.01, f * 3.2], 1.2, 0.35, [1, 0.3, 0.12])) for i, f in enumerate(notes)])


def sfx_buzz():
    n = int(0.4 * SR)
    return tone(110, 0.4, 'square') * env(n, 0.005, 0.05, 0.8, 0.05) * 0.5


def sfx_button():
    return modal([900, 2100], 0.12, 0.02) + noise(0.12) * decay(int(0.12 * SR), 0.003) * 0.5


def sfx_box_open():
    return mix((0, sfx_button()), (0.15, creak(0.5, 300, 200) * 0.5), (0.5, sfx_chime() * 0.7))


def sfx_squirt():
    n = int(0.55 * SR)
    f = lambda t: 300 + 600 * np.exp(-t * 8)
    gurgle = tone(f, 0.55, 'sine') * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t_(0.55)))
    return (gurgle * 0.6 + lp_fast(noise(0.55), 1500) * 0.6) * env(n, 0.01, 0.4, 0.2, 0.1)


def sfx_shimmer():
    parts = []
    for i in range(10):
        f = 1200 + 160 * i
        parts.append((i * 0.04, tone(f, 0.6, 'sine') * decay(int(0.6 * SR), 0.18) * 0.4))
    hum = tone(220, 1.0, 'tri') * env(int(1.0 * SR), 0.2, 0.3, 0.5, 0.4) * 0.3
    return mix((0, hum), *parts)


def sfx_rattle():
    parts = [(rng.uniform(0, 0.4), modal([2400 + rng.uniform(-300, 300), 4100], 0.05, 0.008) * rng.uniform(0.3, 1))
             for _ in range(16)]
    return mix(*parts)


def sfx_paper():
    n = int(0.5 * SR)
    x = noise(0.5) * (0.5 + 0.5 * (rng.uniform(0, 1, n) > 0.7))
    return lp_fast(x, 3500) * env(n, 0.02, 0.3, 0.3, 0.1)


def sfx_stone():
    n = int(1.6 * SR)
    scrape = lp_fast(noise(1.6), 500) * env(n, 0.2, 1.0, 0.7, 0.3)
    rumble = tone(lambda t: 50 + 10 * np.sin(t * 7), 1.6, 'tri') * env(n, 0.3, 1.0, 0.6, 0.3) * 0.5
    return mix((0, scrape + rumble), (1.45, thunk(70, 0.4)))


def sfx_clink():
    return mix((0, modal([2600, 4400, 6100], 0.4, 0.08)), (0.12, modal([2600, 4400], 0.3, 0.06) * 0.5),
               (0.2, modal([2600, 4400], 0.25, 0.05) * 0.3))


def sfx_coin_in():
    return mix((0, modal([2000, 3600], 0.15, 0.03)), (0.12, sfx_clink() * 0.4),
               (0.35, tone(880, 0.12, 'square') * 0.25), (0.47, tone(1320, 0.2, 'square') * 0.25))


def sfx_crank():
    parts = [(i * 0.09, modal([700, 1500], 0.07, 0.01) * (0.6 + 0.4 * (i % 2))) for i in range(22)]
    return mix(*parts)


def sfx_whoosh():
    n = int(0.6 * SR)
    return lp_fast(noise(0.6), 2000) * np.sin(np.linspace(0, np.pi, n)) ** 2


def sfx_bleeps():
    parts = []
    for i, f in enumerate([523, 659, 784, 1047, 784, 1047, 1319]):
        parts.append((i * 0.07, tone(f, 0.07, 'square') * 0.3))
    return mix(*parts)


def sfx_jump():
    """A quick rising blip, for the meatball's hop."""
    n = int(0.12 * SR)
    f = np.linspace(330, 880, n)
    w = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return w * np.linspace(1, 0, n) * 0.25


def sfx_splat():
    """A wet thud, when the meatball hits something."""
    return mix((0, noise(0.18) * env(int(0.18 * SR), 0.002, 0.05, 0.3, 0.1) * 0.5),
               (0, tone(110, 0.2, 'sine') * env(int(0.2 * SR), 0.002, 0.1, 0.2, 0.08) * 0.6))


def sfx_sad():
    return mix((0, tone(392, 0.2, 'square') * 0.3), (0.22, tone(370, 0.2, 'square') * 0.3),
               (0.44, tone(349, 0.2, 'square') * 0.3), (0.66, tone(330, 0.5, 'square') * env(int(0.5 * SR), 0.01, 0.3, 0.4, 0.2) * 0.3))


def sfx_fanfare():
    notes = [(0, 523), (0.15, 659), (0.3, 784), (0.45, 1047)]
    parts = [(o, (tone(f, 0.5, 'saw') * 0.3 + tone(f * 2, 0.5, 'sine') * 0.15) * env(int(0.5 * SR), 0.01, 0.2, 0.6, 0.2))
             for o, f in notes]
    parts.append((0.6, (tone(1047, 1.2, 'saw') * 0.3 + tone(784, 1.2, 'saw') * 0.2 + tone(523, 1.2, 'saw') * 0.2)
                  * env(int(1.2 * SR), 0.02, 0.4, 0.6, 0.5)))
    return lp_fast(mix(*parts), 3500)


def sfx_slurp():
    n = int(1.0 * SR)
    f = lambda t: 300 + 900 * t
    s = tone(f, 1.0, 'sine') * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t_(1.0)))
    return (s * 0.4 + lp_fast(noise(1.0), 2500) * 0.4) * env(n, 0.05, 0.6, 0.5, 0.2)


def sfx_phone():
    """One ring of an old bell telephone: the clapper rattling between two bells."""
    dur = 1.3
    t = t_(dur)
    ring_len = 0.95
    bells = sum(amp * np.sin(2 * np.pi * f * t) * np.exp(-t * dk)
                for f, amp, dk in ((1180, 0.5, 2.0), (1420, 0.4, 2.4), (2950, 0.18, 4.0), (3870, 0.1, 5.0)))
    # the clapper strikes about 25 times a second; each strike re-excites the bells
    strikes = np.zeros_like(t)
    k = np.arange(int(ring_len * 25))
    strikes[(k / 25 * SR).astype(int)] = 1.0
    hit = np.exp(-np.arange(int(0.04 * SR)) / (0.012 * SR))
    clap = np.convolve(strikes, hit)[:len(t)]
    ring = np.sin(2 * np.pi * 1180 * t) * 0.5 + np.sin(2 * np.pi * 1420 * t) * 0.45 + np.sin(2 * np.pi * 2950 * t) * 0.15
    body = ring * np.clip(clap, 0, 1)
    tail = (t > ring_len) * bells * np.exp(-(t - ring_len).clip(0) * 6)
    out = body + tail * 0.6 + noise(dur) * np.clip(clap, 0, 1) * 0.03
    return out / np.max(np.abs(out)) * 0.7 * env(len(t), 0.003, 0.0, 1.0, 0.15)


def sfx_step_creak():
    return creak(0.3, 220, 260) * 0.5


# ------------------------------------------------------------------ music
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def hz(name):
    """'A4' -> 440."""
    n, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] - 9) / 12 + (octv - 4))


def mandolin(freq, dur):
    a = pluck(freq, dur, 0.4)
    b = pluck(freq * 1.003, dur, 0.4)            # doubled course
    return (a + b) * 0.5


def accordion(freq, dur):
    n = int(dur * SR)
    s = tone(freq, dur, 'saw') * 0.5 + tone(freq * 1.004, dur, 'saw') * 0.4 + tone(freq * 2, dur, 'square') * 0.08
    return lp_fast(s, 2200) * env(n, 0.03, 0.1, 0.8, 0.06)


def organ(freq, dur):
    n = int(dur * SR)
    s = sum(tone(freq * h, dur, 'sine') * a for h, a in ((1, 1), (2, 0.5), (3, 0.25), (4, 0.2), (0.5, 0.4)))
    return s * env(n, 0.06, 0.2, 0.8, 0.15)


def bass(freq, dur):
    return pluck(freq, dur, 0.1) * 1.2


def music_title():
    """A tarantella-ish theme in A minor for mandolin and accordion, 6/8,
    looping cleanly after 8 bars."""
    beat = 0.17                                   # one eighth note
    bar = beat * 6
    melody = [
        'A4', 'C5', 'E5', 'A5', 'G5', 'E5', 'F5', 'E5', 'D5', 'C5', 'B4', 'A4',
        'G#4', 'B4', 'E5', 'G#5', 'F5', 'E5', 'D5', 'C5', 'B4', 'A4', 'B4', 'G#4',
        'A4', 'C5', 'E5', 'A5', 'B5', 'C6', 'B5', 'A5', 'G5', 'F5', 'E5', 'D5',
        'C5', 'D5', 'E5', 'D5', 'C5', 'B4', 'A4', 'E4', 'G#4', 'A4', '-', '-',
    ]
    chords = [('A3', 'C4', 'E4'), ('A3', 'C4', 'E4'), ('E3', 'G#3', 'B3'), ('E3', 'G#3', 'B3'),
              ('A3', 'C4', 'E4'), ('F3', 'A3', 'C4'), ('D3', 'F3', 'A3'), ('E3', 'G#3', 'B3')]
    roots = ['A2', 'A2', 'E2', 'E2', 'A2', 'F2', 'D2', 'E2']
    length = bar * 8
    parts = []
    for i, nname in enumerate(melody):
        if nname != '-':
            parts.append((i * beat, mandolin(hz(nname), beat * 1.6) * 0.9))
    for b, ch in enumerate(chords):
        for k in range(2):                        # two dotted-quarter pulses per bar
            o = b * bar + k * beat * 3
            parts.append((o, bass(hz(roots[b]), beat * 1.5) * 0.9))
            for nname in ch:
                parts.append((o + beat, accordion(hz(nname), beat * 0.9) * 0.22))
                parts.append((o + beat * 2, accordion(hz(nname), beat * 0.9) * 0.22))
    # a tambourine on every beat
    for i in range(48):
        jingle = lp_fast(noise(0.06), 6000) * decay(int(0.06 * SR), 0.015) * (0.25 if i % 3 == 0 else 0.12)
        parts.append((i * beat, jingle))
    out = mix(*parts, length=length)
    return out[:int(length * SR)]


def music_ending():
    """A slow, grand organ chorale: four chords and a picardy finish."""
    chords = [('A2', 'E3', 'A3', 'C4', 'E4'), ('F2', 'C3', 'A3', 'C4', 'F4'),
              ('D2', 'A2', 'F3', 'A3', 'D4'), ('E2', 'B2', 'G#3', 'B3', 'E4'),
              ('A2', 'E3', 'A3', 'C#4', 'E4')]
    parts = []
    for i, ch in enumerate(chords):
        dur = 1.6 if i < 4 else 3.2
        for nname in ch:
            parts.append((i * 1.6, organ(hz(nname), dur) * 0.25))
    return lp_fast(mix(*parts), 3000)


def music_crypt():
    """The arcade: a quiet loop of chip bleeps over a low drone."""
    beat = 0.2
    seq = ['A3', 'E4', 'A4', 'C5', 'B4', 'E4', 'G4', 'B4', 'F4', 'C5', 'A4', 'F4', 'E4', 'B4', 'G#4', 'E4'] * 2
    parts = []
    for i, nname in enumerate(seq):
        parts.append((i * beat, tone(hz(nname), beat * 0.8, 'square') * env(int(beat * 0.8 * SR), 0.005, 0.1, 0.3, 0.05) * 0.12))
    length = beat * len(seq)
    drone = (tone(hz('A1'), length, 'saw') * 0.15 + tone(hz('E2'), length, 'tri') * 0.15)
    drone = lp_fast(drone, 400)
    out = mix((0, drone), *parts, length=length)[:int(length * SR)]
    # the loop plays twice, then fades away over the second half of the second play
    out = np.concatenate([out, out])
    n = len(out) // 4
    out[-n:] *= np.linspace(1, 0, n) ** 1.5
    return out


EFFECTS = {
    'aWardOpen': sfx_wardrobe_open, 'aWardClose': sfx_wardrobe_close, 'aClack': sfx_clack,
    'aRatchet': sfx_ratchet, 'aReset': sfx_reset, 'aDrawer': sfx_drawer, 'aChime': sfx_chime,
    'aBuzz': sfx_buzz, 'aButton': sfx_button, 'aBoxOpen': sfx_box_open, 'aSquirt': sfx_squirt,
    'aShimmer': sfx_shimmer, 'aRattle': sfx_rattle, 'aPaper': sfx_paper, 'aStone': sfx_stone,
    'aClink': sfx_clink, 'aCoinIn': sfx_coin_in, 'aCrank': sfx_crank, 'aWhoosh': sfx_whoosh,
    'aBleeps': sfx_bleeps, 'aSad': sfx_sad, 'aFanfare': sfx_fanfare, 'aSlurp': sfx_slurp,
    'aPhone': sfx_phone, 'aJump': sfx_jump, 'aSplat': sfx_splat,
}
# ------------------------------------------------------------------ more effects
def _norm(x, peak=0.8):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def sfx_rip():
    """The tapestry's thread pulled out: a run of little tearing snaps."""
    parts = []
    t = 0.0
    for k in range(14):
        n = noise(0.03) * decay(int(0.03 * SR), 0.008)
        parts.append((t, n * (0.5 + 0.5 * (k % 3 == 0))))
        t += 0.035 + 0.02 * ((k * 7) % 3)
    x = mix(*parts)
    return _norm(x - lp_fast(x, 900), 0.6)


def sfx_rumble():
    """A little mountain heaving up out of the sod."""
    d = 1.1
    n = lp_fast(lp_fast(noise(d), 120), 180)
    wob = 1 + 0.3 * np.sin(2 * np.pi * 7 * t_(d))
    return _norm(n * wob * env(int(d * SR), 0.15, 0.4, 0.6, 0.4), 0.9)


def sfx_splash():
    """The marinara river parting: a swoosh that opens up."""
    d = 0.8
    n = noise(d)
    lo = lp_fast(n, 1800) - lp_fast(n, 300)
    return _norm(lo * env(int(d * SR), 0.05, 0.25, 0.4, 0.45), 0.6)


def sfx_star():
    """The purple star: a rising sparkle."""
    parts = [(i * 0.06, tone(f, 0.5, 'sine') * decay(int(0.5 * SR), 0.18) * 0.25)
             for i, f in enumerate([1047, 1319, 1568, 2093, 2637, 3136])]
    return _norm(mix(*parts), 0.6)


def sfx_cheer():
    """The tiny folk cheering: lots of very small, very high voices."""
    parts = []
    r = np.random.default_rng(3)
    for k in range(22):
        f0 = r.uniform(900, 1600)
        d = r.uniform(0.12, 0.25)
        f = lambda t, f0=f0: f0 * (1 + 0.25 * np.sin(2 * np.pi * 9 * t)) * (1 + 0.4 * t)
        parts.append((r.uniform(0, 0.6), tone(f, d, 'tri') * env(int(d * SR), 0.02, 0.05, 0.6, 0.05) * 0.12))
    return _norm(mix(*parts), 0.55)


def sfx_dig():
    """Tiny shovels in the sod."""
    parts = []
    for k in range(10):
        n = lp_fast(noise(0.06), 2500) * decay(int(0.06 * SR), 0.02)
        parts.append((k * 0.11 + 0.03 * (k % 2), n))
    return _norm(mix(*parts), 0.5)


def sfx_choir():
    """The ordination: a holy "aaah" chord."""
    d = 2.2
    t = t_(d)
    out = np.zeros(len(t))
    for f in (220, 277.2, 329.6, 440):
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t + f)
        w = tone(lambda tt, f=f: f * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * tt)), d, 'saw')
        out += lp_fast(w, 1400)
    return _norm(out * env(len(t), 0.4, 0.3, 0.8, 0.8), 0.5)


def sfx_honk():
    """A clown's bulb horn: honk-honk."""
    def one(f):
        d = 0.18
        w = tone(f, d, 'square') * 0.6 + tone(f * 1.5, d, 'saw') * 0.4
        return lp_fast(w, 1600) * env(int(d * SR), 0.01, 0.05, 0.8, 0.05)
    return _norm(mix((0, one(370)), (0.24, one(330))), 0.7)


def sfx_roar():
    """The T. Rex's roar, eight bits of it."""
    d = 1.0
    f = lambda t: 160 * (1 - 0.45 * t) + 25 * np.sin(2 * np.pi * 23 * t)
    w = tone(f, d, 'saw') * 0.6 + lp_fast(noise(d), 700) * 0.6
    return _norm(w * env(int(d * SR), 0.05, 0.2, 0.7, 0.4), 0.85)


def sfx_cluck():
    """A chicken: buk-buk-bukAWK."""
    def buk(f, d):
        return tone(lambda t: f * (1 - 0.3 * t / d), d, 'square') * env(int(d * SR), 0.005, 0.03, 0.5, 0.02)
    x = mix((0, buk(520, 0.07)), (0.13, buk(520, 0.07)), (0.26, buk(500, 0.07)),
            (0.42, tone(lambda t: 700 + 500 * t, 0.25, 'square') * env(int(0.25 * SR), 0.01, 0.05, 0.6, 0.08)))
    return _norm(lp_fast(x, 2500), 0.6)


def sfx_boot():
    """The old computer switching on: a click, a hum, a beep."""
    hum = (tone(60, 1.0, 'sine') * 0.5 + tone(120, 1.0, 'sine') * 0.2) * env(int(1.0 * SR), 0.2, 0.2, 0.6, 0.3)
    click = noise(0.02) * decay(int(0.02 * SR), 0.004)
    beep = tone(1000, 0.15, 'square') * 0.25
    return _norm(mix((0, click), (0.02, hum), (0.7, beep)), 0.6)


def sfx_cork():
    """A cork popping, and the fizz."""
    pop = tone(lambda t: 900 - 3000 * t, 0.08, 'sine') * decay(int(0.08 * SR), 0.02)
    fizz = (noise(1.0) - lp_fast(noise(1.0), 3000)) * env(int(1.0 * SR), 0.02, 0.2, 0.4, 0.5) * 0.3
    return _norm(mix((0, pop), (0.05, fizz)), 0.7)


def sfx_plop():
    """The meatball landing in the bowl of spaghetti."""
    d = 0.25
    w = tone(lambda t: 300 + 600 * t, d, 'sine') * decay(int(d * SR), 0.06)
    return _norm(w + lp_fast(noise(d), 600) * decay(int(d * SR), 0.03) * 0.5, 0.7)


def sfx_point():
    """A small blip: an obstacle cleared."""
    return tone(1568, 0.06, 'square') * env(int(0.06 * SR), 0.002, 0.03, 0.3, 0.02) * 0.2


EFFECTS.update({'aRip': sfx_rip, 'aRumble': sfx_rumble, 'aSplash': sfx_splash, 'aStar': sfx_star,
                'aCheer': sfx_cheer, 'aDig': sfx_dig, 'aChoir': sfx_choir, 'aHonk': sfx_honk,
                'aRoar': sfx_roar, 'aCluck': sfx_cluck, 'aBoot': sfx_boot, 'aCork': sfx_cork,
                'aPlop': sfx_plop, 'aPoint': sfx_point})


MUSIC = {'aMusTitle': music_title, 'aMusCrypt': music_crypt, 'aMusEnding': music_ending}


# ------------------------------------------------------------------ sounds from the first game
HP_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'hotel-paradiso-scummc', 'assets')


def read_voc(name):
    """An 8-bit unsigned Creative VOC (block type 1) from Hotel Paradiso, resampled to SR."""
    b = open(os.path.join(HP_ASSETS, name), 'rb').read()
    p = int.from_bytes(b[20:22], 'little')
    out, rate = [], None
    while p < len(b) and b[p] != 0:
        t = b[p]; n = int.from_bytes(b[p + 1:p + 4], 'little'); body = b[p + 4:p + 4 + n]
        if t == 1:
            rate = 1000000 / (256 - body[0])
            out.append(np.frombuffer(body[2:], dtype=np.uint8))
        elif t == 2:
            out.append(np.frombuffer(body, dtype=np.uint8))
        p += 4 + n
    x = (np.concatenate(out).astype(float) - 128) / 128
    m = int(len(x) * SR / rate)
    return np.interp(np.linspace(0, len(x) - 1, m), np.arange(len(x)), x)


def tv_click():
    """The first game's click, then a quick burst of static as the channel changes."""
    c = read_voc('lamp_click.voc')
    n = int(0.18 * SR)
    st = np.random.default_rng(3).uniform(-1, 1, n) * np.linspace(0.5, 0, n)
    return np.concatenate([c[:int(0.08 * SR)], st])


EFFECTS.update({
    'aTvClick': lambda: tv_click(),
    'aLampClick': lambda: read_voc('lamp_click.voc'),
    'aFridge': lambda: read_voc('fridge.voc'),
    'aPhoneDial': lambda: read_voc('phone_dial.voc'),
    'aPhoneHang': lambda: read_voc('phone_hang.voc'),
})


# ------------------------------------------------------------------ second pass: wetter, more natural sounds
# (each has its own random generator, so remaking one never changes the others)
from scipy.signal import butter, sosfilt


def _bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)


def _hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)


def _reson(x, f, bw):
    """A two-pole resonator (a formant) at f Hz with bandwidth bw Hz."""
    r = math.exp(-math.pi * bw / SR)
    th = 2 * math.pi * f / SR
    return lfilter([1 - r], [1, -2 * r * math.cos(th), r * r], x)


def _bubble(f0, dur, rise=2.0, tau=None):
    """One liquid bubble (a Minnaert resonance): a sine whose pitch rises as it decays."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    tau = tau or 0.4 / f0 ** 0.6
    ph = 2 * np.pi * np.cumsum(f0 * (1 + rise * t / dur)) / SR
    return np.sin(ph) * np.exp(-t / tau)


def _bubbles(r, count, span, flo, fhi, amp=0.5):
    parts = []
    for _ in range(count):
        f = math.exp(r.uniform(math.log(flo), math.log(fhi)))
        parts.append((r.uniform(0, span), _bubble(f, 0.06, r.uniform(0.5, 3)) * amp * r.uniform(0.3, 1)))
    return mix(*parts)


def sfx_squirt2():
    """A pump of sauce: a wet squelch from the pump, a splutter of sauce, bubbles popping in the bowl."""
    r = np.random.default_rng(101)
    d = 0.6
    n = int(d * SR)
    t = np.arange(n) / SR
    # the squelch: noise through a mouth-like formant that sweeps down as the pump presses
    sq = r.uniform(-1, 1, n) * env(n, 0.01, 0.12, 0.25, 0.25)
    sweep = np.zeros(n)
    for f0, f1, bw, a in ((1400, 500, 220, 1.0), (2600, 1500, 300, 0.5)):
        f = f0 + (f1 - f0) * np.clip(t / 0.25, 0, 1)
        # time-varying formant: filter in short blocks
        blk = 256
        for i in range(0, n, blk):
            seg = sq[i:i + blk]
            sweep[i:i + blk] += _reson(seg, float(f[i]), bw) * a
    sweep = _norm(sweep, 0.5)
    # sputter: the sauce coming out in uneven gobs
    gobs = []
    for k in range(7):
        o = 0.05 + k * 0.035 + r.uniform(0, 0.02)
        g = _bp(r.uniform(-1, 1, int(0.03 * SR)), 300, 1800) * decay(int(0.03 * SR), 0.008)
        gobs.append((o, g * r.uniform(0.3, 0.7)))
    # bubbles in the bowl
    bub = _bubbles(r, 18, 0.45, 350, 1500, 0.35)
    out = mix((0, sweep), (0, mix(*gobs) * 0.6), (0.08, bub))
    return _norm(lp_fast(out, 5000), 0.7)


def sfx_slurp2():
    """Slurping sauce off a rigatone: a sucked, gargly airflow rising in pitch, and a smack."""
    r = np.random.default_rng(202)
    d = 1.0
    n = int(d * SR)
    t = np.arange(n) / SR
    air = r.uniform(-1, 1, n)
    # the slurp: turbulent air through a narrowing mouth, so the resonance climbs
    out = np.zeros(n)
    blk = 200
    for i in range(0, n, blk):
        u = t[i] / d
        f1 = 500 + 1300 * u ** 1.3
        f2 = 1500 + 1500 * u
        seg = air[i:i + blk]
        out[i:i + blk] = _reson(seg, f1, 160) + _reson(seg, f2, 260) * 0.5
    # liquid gets dragged in with it: amplitude flutters with bubbles bursting
    flutter = 0.45 + 0.55 * np.abs(np.sin(2 * np.pi * (11 + 6 * t) * t + r.uniform(0, 6)))
    out = _norm(out, 0.5) * flutter * env(n, 0.06, 0.1, 0.9, 0.12) * np.clip(1.1 - t, 0, 1)
    bub = _bubbles(r, 26, 0.75, 500, 2200, 0.25)
    # the smack at the end: lips parting
    smack = _bp(r.uniform(-1, 1, int(0.03 * SR)), 900, 4000) * decay(int(0.03 * SR), 0.004)
    res = mix((0, out), (0.05, bub), (0.9, smack * 0.8))
    return _norm(res, 0.7)


def sfx_dig2():
    """Tiny shovels biting into the sod: gritty crunches and earth tossed aside, no thuds."""
    r = np.random.default_rng(303)
    parts = []
    o = 0.0
    for k in range(6):
        # the bite: a dense crackle of grains, high and crunchy (tiny shovels)
        d = 0.09
        nn = int(d * SR)
        grains = np.zeros(nn)
        for _ in range(140):
            i = int(r.uniform(0, 1) ** 1.6 * (nn - 40))
            grains[i:i + 30] += r.uniform(-1, 1) * np.exp(-np.arange(30) / 4)
        bite = _bp(grains, 1500, 7000) * env(nn, 0.004, 0.05, 0.3, 0.03)
        scrape = _bp(r.uniform(-1, 1, nn), 2500, 6000) * env(nn, 0.01, 0.05, 0.2, 0.03) * 0.25
        # the toss: a softer spray of crumbs landing a moment later
        dt = 0.16
        nt = int(dt * SR)
        crumbs = np.zeros(nt)
        for _ in range(45):
            i = int(r.uniform(0, nt - 40))
            crumbs[i:i + 25] += r.uniform(-1, 1) * np.exp(-np.arange(25) / 3)
        toss = _bp(crumbs, 2000, 8000) * env(nt, 0.02, 0.05, 0.6, 0.06) * 0.35
        parts += [(o, (bite + scrape) * r.uniform(0.7, 1)), (o + 0.11, toss)]
        o += r.uniform(0.17, 0.24)
    return _norm(mix(*parts), 0.55)


def _voice(r, f0s, vowels, dur, breath=0.15, jitter=0.02):
    """A tiny formant voice. f0s and vowels are lists of (time 0..1, value) keyframes;
    vowels are (F1, F2, F3) in Hz, already scaled up for a very small throat."""
    n = int(dur * SR)
    u = np.arange(n) / n
    def kf(keys, i):
        ts = [k[0] for k in keys]
        return np.interp(u, ts, [k[1][i] if isinstance(k[1], tuple) else k[1] for k in keys])
    f0 = kf(f0s, 0) * (1 + jitter * np.convolve(r.normal(0, 1, n), np.ones(200) / 200, 'same') * 10)
    ph = np.cumsum(f0) / SR
    # a glottal pulse: sharp closing edge, rounded opening
    g = (ph % 1.0)
    src = np.where(g < 0.6, 0.5 - 0.5 * np.cos(np.pi * g / 0.6), np.cos(np.pi * (g - 0.6) / 0.8)) - 0.3
    src = np.diff(src, prepend=src[0]) * 30
    src += r.normal(0, 1, n) * breath
    F = [kf(vowels, i) for i in range(3)]
    out = np.zeros(n)
    blk = 128
    for i in range(0, n, blk):
        seg = src[i:i + blk]
        out[i:i + blk] = (_reson(seg, F[0][i], 90) * 1.0 + _reson(seg, F[1][i], 120) * 0.6
                          + _reson(seg, F[2][i], 180) * 0.3)
    return out


def sfx_cheer2():
    """The tiny folk cheering: a little crowd of high voices going "yaaay!" and "woo!"."""
    r = np.random.default_rng(404)
    k = 1.55                                   # small people, small throats: every formant up
    AH, EH, EE, OO, AY = (730, 1100, 2450), (530, 1840, 2480), (300, 2300, 3000), (330, 870, 2240), (660, 1700, 2400)
    sc = lambda v: tuple(x * k for x in v)
    parts = []
    for v in range(16):
        dur = r.uniform(0.45, 0.8)
        f0 = r.uniform(380, 620)
        if r.uniform() < 0.65:                 # "yaaay": y-glide into ah, ending in ee
            vow = [(0, sc(EE)), (0.12, sc(AH)), (0.7, sc(AY)), (1, sc(EE))]
            pitch = [(0, f0 * 0.9), (0.25, f0 * 1.25), (0.8, f0 * 1.1), (1, f0 * 0.8)]
        else:                                  # "woo!": rising hoot
            vow = [(0, sc(OO)), (1, sc(OO))]
            pitch = [(0, f0 * 0.9), (0.4, f0 * 1.45), (1, f0 * 1.2)]
        x = _voice(r, pitch, vow, dur, breath=0.2)
        nn = len(x)
        x *= env(nn, 0.04, 0.1, 0.8, 0.18)
        parts.append((r.uniform(0, 0.35), _norm(x, r.uniform(0.25, 0.5))))
    crowd = mix(*parts)
    # a few claps from very small hands
    claps = []
    for c in range(14):
        cl = _bp(r.uniform(-1, 1, int(0.02 * SR)), 2000, 7000) * decay(int(0.02 * SR), 0.003)
        claps.append((r.uniform(0.05, 0.9), cl * r.uniform(0.15, 0.3)))
    out = mix((0, _hp(crowd, 250)), *claps)
    n = len(out)
    out *= np.concatenate([np.ones(n - int(0.15 * SR)), np.linspace(1, 0, int(0.15 * SR))])
    return _norm(out, 0.6)


def sfx_cluck2():
    """A chicken: bok, bok, bok... ba-GAWK! Rough, nasal, with a squawk at the end."""
    r = np.random.default_rng(505)
    def call(dur, pitch, vowel, rough=0.4, breath=0.25):
        x = _voice(r, pitch, vowel, dur, breath=breath, jitter=0.05)
        n = len(x)
        # roughness: every other glottal pulse weaker (a chicken's rattly syrinx)
        t = np.arange(n) / SR
        f = np.interp(np.arange(n) / n, [p[0] for p in pitch], [p[1] for p in pitch])
        x *= 1 - rough * (0.5 + 0.5 * np.sign(np.sin(np.pi * np.cumsum(f) / SR)))
        return x
    BOK = [(0, (450, 1000, 2600)), (1, (380, 800, 2400))]
    AH = [(0, (500, 1200, 2700)), (0.25, (850, 1500, 2900)), (1, (750, 1300, 2700))]
    def bok(f):
        x = call(0.075, [(0, f * 1.15), (1, f * 0.8)], BOK, rough=0.35)
        n = len(x)
        return x * env(n, 0.004, 0.03, 0.4, 0.02)
    def gawk():
        d = 0.36
        x = call(d, [(0, 480), (0.15, 820), (0.5, 760), (1, 520)], AH, rough=0.55, breath=0.35)
        n = len(x)
        # the "g" onset
        x[:int(0.015 * SR)] *= np.linspace(0, 1, int(0.015 * SR))
        return x * env(n, 0.01, 0.08, 0.7, 0.12)
    out = mix((0, _norm(bok(330), 0.5)), (0.17, _norm(bok(340), 0.5)), (0.33, _norm(bok(320), 0.45)),
              (0.5, _norm(bok(360), 0.35)), (0.58, _norm(gawk(), 0.8)))
    return _norm(_hp(out, 200), 0.7)


def music_ending2():
    """The ending: the title's tarantella again, now in A major and bright, finishing on a big chord."""
    beat = 0.16
    bar = beat * 6
    melody = [
        'A4', 'C#5', 'E5', 'A5', 'G#5', 'E5', 'F#5', 'E5', 'D5', 'C#5', 'B4', 'A4',
        'G#4', 'B4', 'E5', 'G#5', 'F#5', 'E5', 'D5', 'C#5', 'B4', 'A4', 'B4', 'G#4',
        'A4', 'C#5', 'E5', 'A5', 'B5', 'C#6', 'B5', 'A5', 'G#5', 'F#5', 'E5', 'D5',
        'C#5', 'D5', 'E5', 'F#5', 'G#5', 'B5', 'A5', '-', '-', '-', '-', '-',
    ]
    chords = [('A3', 'C#4', 'E4'), ('D3', 'F#3', 'A3'), ('E3', 'G#3', 'B3'), ('E3', 'G#3', 'B3'),
              ('A3', 'C#4', 'E4'), ('F#3', 'A3', 'C#4'), ('D3', 'F#3', 'A3'), ('E3', 'G#3', 'B3')]
    roots = ['A2', 'D2', 'E2', 'E2', 'A2', 'F#2', 'D2', 'E2']
    parts = []
    for i, nname in enumerate(melody):
        if nname != '-':
            parts.append((i * beat, mandolin(hz(nname), beat * 1.6) * 0.9))
            if i >= 24:                           # second half: an octave-up sparkle on top
                parts.append((i * beat, mandolin(hz(nname) * 2, beat * 1.2) * 0.25))
    for b, ch in enumerate(chords[:4] + chords[4:]):
        for k in range(2):
            o = b * bar + k * beat * 3
            parts.append((o, bass(hz(roots[b]), beat * 1.5) * 0.9))
            for nname in ch:
                parts.append((o + beat, accordion(hz(nname), beat * 0.9) * 0.22))
                parts.append((o + beat * 2, accordion(hz(nname), beat * 0.9) * 0.22))
    for i in range(48):
        jingle = lp_fast(noise(0.06), 6000) * decay(int(0.06 * SR), 0.015) * (0.25 if i % 3 == 0 else 0.12)
        parts.append((i * beat, jingle))
    # the finish: a big held A major chord, accordion swell, mandolin tremolo and a last tambourine shake
    end = 8 * bar - beat * 5
    for nname in ('A2', 'E3', 'A3', 'C#4', 'E4', 'A4'):
        parts.append((end, accordion(hz(nname), 2.4) * 0.2 * env(int(2.4 * SR), 0.02, 0.3, 0.8, 0.9)))
    parts.append((end, bass(hz('A1'), 2.0) * 1.0))
    for j in range(16):
        f = hz('C#6') if j % 2 else hz('A5')
        parts.append((end + j * 0.07, mandolin(f, 0.25) * 0.35 * (1 - j / 18)))
    shake = lp_fast(noise(0.8), 6000) * env(int(0.8 * SR), 0.05, 0.1, 0.5, 0.5) * 0.18
    parts.append((end, shake))
    out = mix(*parts)
    n = int(0.6 * SR)
    out[-n:] *= np.linspace(1, 0, n)
    return out


def _instead(old, new):
    """Use the new sound, but still run the old one first so the shared random generator
    stays in step and every other sound comes out exactly as before."""
    return lambda: (old(), new())[1]


EFFECTS.update({'aSquirt': _instead(sfx_squirt, sfx_squirt2), 'aSlurp': _instead(sfx_slurp, sfx_slurp2),
                'aDig': _instead(sfx_dig, sfx_dig2), 'aCheer': _instead(sfx_cheer, sfx_cheer2),
                'aCluck': _instead(sfx_cluck, sfx_cluck2), 'aHonk': _instead(sfx_honk, lambda: read_voc('honk.voc'))})
def _choir_ah(freq, dur):
    """One choir voice singing "aah": a saw with vibrato through the formants of the vowel."""
    t = t_(dur)
    w = tone(lambda tt: freq * (1 + 0.007 * np.sin(2 * np.pi * 5.0 * tt + freq)), dur, 'saw')
    w += tone(lambda tt: freq * 1.003 * (1 + 0.007 * np.sin(2 * np.pi * 5.4 * tt)), dur, 'saw')
    v = _reson(w, 750, 120) + _reson(w, 1150, 150) * 0.6 + _reson(w, 2600, 250) * 0.25
    return v * env(len(t), 0.25, 0.2, 0.85, 0.35)


def music_ending3():
    """The ending: the old organ chorale with a choir, now in A major and climbing,
    with the top voice rising to a bright held finish."""
    step = 1.35
    chords = [('A2', 'E3', 'A3', 'C#4', 'E4'), ('D2', 'A2', 'F#3', 'A3', 'F#4'),
              ('E2', 'B2', 'G#3', 'B3', 'G#4'), ('F#2', 'C#3', 'A3', 'C#4', 'A4'),
              ('D2', 'A2', 'F#3', 'A3', 'B4'), ('E2', 'B2', 'G#3', 'B3', 'B4'),
              ('A2', 'E3', 'A3', 'C#4', 'E4', 'A4', 'C#5')]
    parts = []
    for i, ch in enumerate(chords):
        last = i == len(chords) - 1
        dur = 3.4 if last else step + 0.1
        for nname in ch:
            parts.append((i * step, organ(hz(nname), dur) * 0.2))
        # the choir sings the upper three notes, an octave of warmth over the organ
        for nname in ch[-3:]:
            parts.append((i * step, _choir_ah(hz(nname), dur) * 0.05))
    # bells ringing out over the last chord
    end = (len(chords) - 1) * step
    for j, nname in enumerate(['A5', 'C#6', 'E6', 'A6']):
        f = hz(nname)
        parts.append((end + 0.25 + j * 0.18, modal([f, f * 2.76, f * 5.4], 2.2, 0.5, [1, 0.35, 0.15]) * 0.12))
    out = lp_fast(mix(*parts), 3600)
    n = int(1.0 * SR)
    out[-n:] *= np.linspace(1, 0, n) ** 1.5
    return out


MUSIC['aMusEnding'] = _instead(music_ending, music_ending3)  # Room 714's honk, for the clowns
