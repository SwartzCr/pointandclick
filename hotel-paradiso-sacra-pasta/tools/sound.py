"""Every sound effect and both pieces of music, synthesised with numpy and
written as 16-bit mono WAV files (22050 Hz)."""
import io
import math
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
    """A crackly little voice: band-limited noise shaped like syllables."""
    n = int(2.2 * SR)
    syll = (np.sin(2 * np.pi * 4.5 * t_(2.2)) > -0.2).astype(float)
    voice = tone(lambda t: 160 + 40 * np.sin(t * 9), 2.2, 'saw') * syll
    return (lp_fast(voice, 1800) * 0.6 + noise(2.2) * 0.08) * env(n, 0.05, 1.5, 0.7, 0.3)


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
    out = mix((0, drone), *parts, length=length)
    return out[:int(length * SR)]


EFFECTS = {
    'aWardOpen': sfx_wardrobe_open, 'aWardClose': sfx_wardrobe_close, 'aClack': sfx_clack,
    'aRatchet': sfx_ratchet, 'aReset': sfx_reset, 'aDrawer': sfx_drawer, 'aChime': sfx_chime,
    'aBuzz': sfx_buzz, 'aButton': sfx_button, 'aBoxOpen': sfx_box_open, 'aSquirt': sfx_squirt,
    'aShimmer': sfx_shimmer, 'aRattle': sfx_rattle, 'aPaper': sfx_paper, 'aStone': sfx_stone,
    'aClink': sfx_clink, 'aCoinIn': sfx_coin_in, 'aCrank': sfx_crank, 'aWhoosh': sfx_whoosh,
    'aBleeps': sfx_bleeps, 'aSad': sfx_sad, 'aFanfare': sfx_fanfare, 'aSlurp': sfx_slurp,
    'aPhone': sfx_phone,
}
MUSIC = {'aMusTitle': music_title, 'aMusCrypt': music_crypt, 'aMusEnding': music_ending}
