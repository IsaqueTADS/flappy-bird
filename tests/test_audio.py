from array import array
import os
import unittest
from unittest.mock import patch

from audio import Audio, RATE, make_effect, make_music


class SynthesisTests(unittest.TestCase):
    def test_effects_have_expected_duration_and_signal_without_clipping(self):
        for name, duration in (("flap", 0.10), ("point", 0.24), ("hit", 0.20), ("over", 0.72)):
            samples = array("h", make_effect(name))
            self.assertAlmostEqual(len(samples) / RATE, duration, places=3)
            self.assertGreater(max(samples), 1000)
            self.assertLess(max(abs(sample) for sample in samples), 32767)
            self.assertLess(abs(samples[0]), 100)
            self.assertLess(abs(samples[-1]), 100)

    def test_music_is_repeatable_and_leaves_headroom_for_effects(self):
        first = make_music()
        self.assertEqual(first, make_music())
        samples = array("h", first)
        self.assertAlmostEqual(len(samples) / RATE, 32 * 60 / 112, places=3)
        self.assertLess(max(abs(sample) for sample in samples), 24000)
        self.assertGreater(max(samples), 1000)

    def test_disabled_audio_supports_every_game_action(self):
        sound = Audio(enabled=False)
        sound.start_music()
        sound.effect("flap")
        sound.die()
        sound.set_paused(True)
        sound.toggle_music()
        sound.toggle_effects()
        sound.close()
        self.assertFalse(sound.available)


class MixerTests(unittest.TestCase):
    def test_music_and_effects_use_separate_channels(self):
        with patch.dict(os.environ, {"SDL_AUDIODRIVER": "dummy"}):
            sound = Audio()
            if not sound.available:
                self.fail(f"Mixer failed: {sound.error}")
            try:
                self.assertTrue(sound.music_channel.get_busy())
                sound.effect("point")
                self.assertTrue(sound.music_channel.get_busy())
                self.assertTrue(any(sound.mixer.Channel(i).get_busy() for i in range(2, 8)))
                sound.toggle_music()
                self.assertEqual(sound.music_channel.get_volume(), 0)
                sound.set_paused(True)
                sound.set_paused(False)
                sound.die()
                self.assertFalse(sound.music_channel.get_busy())
                self.assertIsNotNone(sound.event_channel.get_queue())
                sound.start_music()
                self.assertTrue(sound.music_channel.get_busy())
            finally:
                sound.close()

    def test_missing_device_does_not_prevent_playing(self):
        with patch.dict(os.environ, {"SDL_AUDIODRIVER": "nonexistent-flappy-test-driver"}):
            sound = Audio()
            self.assertFalse(sound.available)
            self.assertTrue(sound.error)
            sound.effect("flap")
            sound.die()
            sound.close()
