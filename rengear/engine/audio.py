"""Procedural audio.

Every sound and the music loop are synthesised at runtime from pure maths, so
the project ships zero third-party audio and cannot inherit anyone else's
copyright.  If the mixer is unavailable the class degrades to silent no-ops,
which keeps headless tests and machines without a sound card working.
"""

from __future__ import annotations

import array
import math
import random
from typing import Dict, Optional, Sequence, Tuple

from .platform import Backend, SoundHandle

Segment = Tuple[float, float, str, float]  # freq, duration, wave, volume


def _osc(wave: str, phase: float) -> float:
    if wave == "sine":
        return math.sin(phase)
    if wave == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if wave == "triangle":
        return 2.0 / math.pi * math.asin(math.sin(phase))
    if wave == "saw":
        t = (phase / math.tau) % 1.0
        return 2.0 * t - 1.0
    if wave == "noise":
        return random.uniform(-1.0, 1.0)
    return math.sin(phase)


class Synth:
    def __init__(self, sample_rate: int = 22050) -> None:
        self.rate = sample_rate

    def render(self, segments: Sequence[Segment], decay: float = 6.0,
               attack: float = 0.005) -> bytes:
        buf = array.array("h")
        phase = 0.0
        for freq, dur, wave, vol in segments:
            count = int(dur * self.rate)
            for i in range(count):
                t = i / self.rate
                phase += math.tau * freq / self.rate
                env = min(1.0, t / attack) if attack > 0 else 1.0
                env *= math.exp(-decay * t)
                value = _osc(wave, phase) * vol * env
                buf.append(max(-32767, min(32767, int(value * 32767))))
        return buf.tobytes()

    def engine_loop(self, freq: float = 74.0, seconds: float = 0.30,
                    vol: float = 0.30) -> bytes:
        """A seamless, harmonically rich loop for the car engine."""
        buf = array.array("h")
        count = int(seconds * self.rate)
        for i in range(count):
            t = i / self.rate
            base = math.tau * freq * t
            sample = (0.55 * _osc("saw", base)
                      + 0.30 * _osc("square", base * 0.5)
                      + 0.15 * _osc("triangle", base * 2.0))
            sample += 0.05 * random.uniform(-1.0, 1.0)
            buf.append(max(-32767, min(32767, int(sample * vol * 32767))))
        return buf.tobytes()

    def music(self, notes: Sequence[Tuple[float, float]], bpm: float = 132.0,
              wave: str = "square", vol: float = 0.16) -> bytes:
        beat = 60.0 / bpm / 2.0  # eighth notes
        segments = []
        for freq, length in notes:
            segments.append((freq, beat * length, wave, vol))
        return self.render(segments, decay=1.6, attack=0.008)


# Note frequencies (A4 = 440).
NOTES = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00,
    "A3": 220.00, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63,
    "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
    "D5": 587.33, "E5": 659.25, "G5": 783.99, "A5": 880.00, "C6": 1046.50,
}


class Audio:
    def __init__(self, backend: Optional[Backend] = None) -> None:
        self.backend = backend
        self.ok = False
        self.enabled = True
        self.sounds: Dict[str, SoundHandle] = {}
        self.music: Optional[SoundHandle] = None
        self.engine: Optional[SoundHandle] = None
        self._music_channel = None
        self._engine_channel = None
        self.volume = 0.7
        self.music_volume = 0.45
        self.engine_volume = 0.0

    def init(self) -> None:
        if self.backend is None or not self.backend.audio_ready():
            self.ok = False
            return
        self.ok = True
        self._build()

    # -- library ----------------------------------------------------------
    def _build(self) -> None:
        synth = Synth(22050)
        library = {
            "select": [(880, 0.04, "square", 0.16)],
            "confirm": [(660, 0.06, "square", 0.20), (990, 0.09, "square", 0.20)],
            "cancel": [(400, 0.06, "square", 0.18), (240, 0.09, "square", 0.16)],
            "count": [(520, 0.14, "square", 0.26)],
            "go": [(880, 0.10, "square", 0.30), (1320, 0.22, "square", 0.28)],
            "skid": [(180, 0.20, "noise", 0.16), (140, 0.20, "saw", 0.12)],
            "crash": [(120, 0.28, "noise", 0.34), (70, 0.36, "saw", 0.26)],
            "bump": [(90, 0.10, "noise", 0.20)],
            "nitro": [(300, 0.35, "saw", 0.16), (900, 0.30, "noise", 0.12)],
            "lap": [(660, 0.10, "triangle", 0.25), (880, 0.12, "triangle", 0.25),
                    (1100, 0.18, "triangle", 0.24)],
            "finish": [(523, 0.14, "triangle", 0.26), (659, 0.14, "triangle", 0.26),
                       (784, 0.14, "triangle", 0.26), (1046, 0.34, "triangle", 0.28)],
            "record": [(523, 0.10, "square", 0.24), (784, 0.10, "square", 0.24),
                       (1046, 0.10, "square", 0.24), (1318, 0.30, "square", 0.26)],
        }
        for name, segments in library.items():
            snd = self.backend.make_sound(synth.render(segments))
            if snd is not None:
                self.sounds[name] = snd

        self.engine = self.backend.make_sound(synth.engine_loop())

        melody = [
            ("A4", 1), ("C5", 1), ("E5", 2), ("D5", 1), ("C5", 1), ("B4", 2),
            ("A4", 1), ("G4", 1), ("A4", 2), ("E4", 1), ("G4", 1), ("A4", 2),
            ("C5", 1), ("B4", 1), ("G4", 2), ("A4", 1), ("C5", 1), ("E5", 2),
            ("G5", 1), ("E5", 1), ("D5", 2), ("C5", 1), ("B4", 1), ("A4", 2),
        ]
        notes = [(NOTES[n], length) for n, length in melody]
        self.music = self.backend.make_sound(synth.music(notes, bpm=138))

    # -- playback ---------------------------------------------------------
    def play(self, name: str, volume: float = 1.0) -> None:
        if not (self.ok and self.enabled):
            return
        snd = self.sounds.get(name)
        if snd is not None:
            snd.set_volume(min(1.0, self.volume * volume))
            snd.play()

    def start_music(self) -> None:
        if not (self.ok and self.enabled and self.music):
            return
        self.stop_music()
        self._music_channel = self.music.play(loops=-1)
        if self._music_channel is not None:
            self._music_channel.set_volume(self.music_volume)

    def stop_music(self) -> None:
        if self.music is not None:
            self.music.stop()

    # -- engine -----------------------------------------------------------
    def start_engine(self) -> None:
        if not (self.ok and self.engine):
            return
        self.stop_engine()
        self._engine_channel = self.engine.play(loops=-1)
        if self._engine_channel is not None:
            self._engine_channel.set_volume(self.engine_volume)

    def stop_engine(self) -> None:
        if self._engine_channel is not None:
            self._engine_channel.stop()
            self._engine_channel = None

    def set_engine(self, level: float) -> None:
        """``level`` in 0..1 — the mixer does not pitch-shift, so this is volume."""
        self.engine_volume = max(0.0, min(1.0, level))
        if self._engine_channel is not None:
            self._engine_channel.set_volume(self.engine_volume)

    def set_enabled(self, value: bool) -> None:
        self.enabled = value
        if not value:
            self.stop_music()
            self.stop_engine()
        elif self.ok:
            self.start_music()
