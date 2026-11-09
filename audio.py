"""Original procedural chiptune and sound effects. No external audio files."""
from array import array
import math
import os
import random
import sys

RATE = 22050


def frequency(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def add_tone(track, start, duration, hz, volume, shape="triangle", end_hz=None):
    """Mix one enveloped oscillator into a floating-point mono track."""
    offset, count = round(start * RATE), round(duration * RATE)
    phase = 0.0
    for i in range(min(count, len(track) - offset)):
        t = i / RATE
        progress = i / max(1, count - 1)
        pitch = hz if end_hz is None else hz + (end_hz - hz) * progress
        phase = (phase + pitch / RATE) % 1.0
        if shape == "square":
            sample = 1.0 if phase < 0.25 else -1 / 3
        elif shape == "sine":
            sample = math.sin(phase * math.tau)
        else:
            sample = 1 - 4 * abs(phase - 0.5)
        envelope = min(1.0, t / 0.005, (duration - t) / 0.025)
        track[offset + i] += sample * volume * max(0, envelope)


def add_noise(track, start, duration, volume, seed=0):
    rng = random.Random(seed)
    offset, count = round(start * RATE), round(duration * RATE)
    for i in range(min(count, len(track) - offset)):
        envelope = (1 - i / count) ** 2 * min(1, i / (RATE * 0.002))
        track[offset + i] += rng.uniform(-1, 1) * volume * envelope


def pcm(track):
    samples = array("h", (round(max(-1, min(1, value)) * 32767) for value in track))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def make_effect(name):
    lengths = {"flap": 0.10, "point": 0.24, "hit": 0.20, "over": 0.72}
    track = [0.0] * round(lengths[name] * RATE)
    if name == "flap":
        add_tone(track, 0, 0.10, 600, 0.45, "square", 1100)
    elif name == "point":
        add_tone(track, 0, 0.11, frequency(84), 0.48, "square")
        add_tone(track, 0.11, 0.13, frequency(91), 0.43, "square")
    elif name == "hit":
        add_noise(track, 0, 0.16, 0.5)
        add_tone(track, 0, 0.20, 150, 0.5, "sine", 45)
    else:
        for i, note in enumerate((76, 72, 67, 60)):
            add_tone(track, i * 0.16, 0.22, frequency(note), 0.38, "triangle")
    return pcm(track)


def make_music():
    """Eight bars, C/Am/F/G harmony, original lead, bass, arpeggio and drums."""
    beat = 60 / 112
    track = [0.0] * round(32 * beat * RATE)
    melodies = (
        (76, 79, 81, 79, 76, 74, 72, 74),
        (76, 79, 84, 83, 79, 76, 74, 72),
        (76, 81, 84, 81, 79, 76, 74, 76),
        (79, 76, 72, 71, 69, 72, 76, 79),
        (77, 81, 84, 81, 77, 76, 74, 72),
        (74, 77, 81, 79, 77, 74, 72, 74),
        (79, 83, 86, 83, 79, 77, 76, 74),
        (74, 71, 67, 71, 74, 79, 76, 72),
    )
    roots = (48, 48, 45, 45, 41, 41, 43, 43)
    chords = ((60, 64, 67), (60, 64, 67), (57, 60, 64), (57, 60, 64),
              (53, 57, 60), (53, 57, 60), (55, 59, 62), (55, 59, 62))
    for bar, melody in enumerate(melodies):
        for step, note in enumerate(melody):
            start = (bar * 4 + step / 2) * beat
            add_tone(track, start, beat * 0.40, frequency(note), 0.14, "square")
            add_tone(track, start, beat * 0.30, frequency(chords[bar][step % 3]), 0.055)
            add_noise(track, start, 0.035, 0.035, bar * 8 + step)
        for step in range(4):
            start = (bar * 4 + step) * beat
            bass = roots[bar] if step % 2 == 0 else roots[bar] + 7
            add_tone(track, start, beat * 0.70, frequency(bass), 0.16)
            if step % 2 == 0:
                add_tone(track, start, 0.11, 110, 0.13, "sine", 38)
            else:
                add_noise(track, start, 0.10, 0.065, bar + step)
    return pcm(track)


class Audio:
    """Reserved music/effect channels; playback never blocks the Tk loop."""

    def __init__(self, music=True, effects=True, enabled=True):
        self.music_enabled, self.effects_enabled = music, effects
        self.available, self.error = False, ""
        self.mixer = None
        self.music_channel = None
        self.backend = "disabled"
        self.paused = False
        if not enabled:
            return
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame.mixer as mixer
            self.mixer = mixer
            mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
            mixer.set_num_channels(8)
            mixer.set_reserved(2)
            self.music_channel = mixer.Channel(0)
            self.event_channel = mixer.Channel(1)
            self.music_sound = mixer.Sound(buffer=make_music())
            self.sounds = {name: mixer.Sound(buffer=make_effect(name)) for name in ("flap", "point", "hit", "over")}
            for sound in self.sounds.values():
                sound.set_volume(0.65)
            self.backend = mixer.get_driver()
            self.available = True
            self.start_music()
        except (ImportError, OSError, RuntimeError) as error:
            self.error = str(error)
            if self.mixer:
                self.mixer.quit()
        except Exception as error:
            # SDL raises pygame.error; an unavailable device must not prevent playing.
            self.error = str(error)
            if self.mixer:
                self.mixer.quit()

    def start_music(self):
        if self.available:
            self.mixer.stop()
            self.music_channel.play(self.music_sound, loops=-1)
            self.music_channel.set_volume(0.36 if self.music_enabled else 0)
            if self.paused:
                self.music_channel.pause()

    def effect(self, name):
        if self.available and self.effects_enabled and not self.paused:
            # Sound.play respects the reserved music and death-sequence channels.
            self.sounds[name].play()

    def die(self):
        if self.available:
            self.mixer.stop()
            if self.effects_enabled:
                self.event_channel.play(self.sounds["hit"])
                self.event_channel.queue(self.sounds["over"])

    def set_paused(self, paused):
        self.paused = paused
        if self.available:
            if paused:
                self.mixer.pause()
            else:
                self.mixer.unpause()

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.available:
            self.music_channel.set_volume(0.36 if self.music_enabled else 0)

    def toggle_effects(self):
        self.effects_enabled = not self.effects_enabled
        if self.available and not self.effects_enabled:
            for channel in range(1, 8):
                self.mixer.Channel(channel).stop()

    def close(self):
        if self.available:
            self.mixer.quit()
            self.available = False
