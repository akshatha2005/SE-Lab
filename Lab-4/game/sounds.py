import array
import math
import pygame


class SoundManager:
    """Generates simple beep sound effects in code (no audio files needed).

    If the audio device can't be opened, every method silently does nothing
    so the game still runs.
    """

    SAMPLE_RATE = 22050

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.SAMPLE_RATE, -16, 1, 512)
            freq, fmt, channels = pygame.mixer.get_init()
            self._rate, self._channels = freq, channels
            self.sounds = {
                "jump": self._make([(440, 0.06), (660, 0.08)]),
                "goal": self._make([(523, 0.09), (659, 0.09), (784, 0.16)]),
                "die": self._make([(330, 0.12), (247, 0.12), (165, 0.25)], square=True),
            }
            self.enabled = True
        except Exception:
            self.enabled = False

    def _make(self, notes, volume=0.3, square=False):
        samples = array.array("h")
        for freq, duration in notes:
            n = int(self._rate * duration)
            for i in range(n):
                wave = math.sin(2 * math.pi * freq * i / self._rate)
                if square:
                    wave = 1.0 if wave >= 0 else -1.0
                fade = 1.0 - i / n  # fade out to avoid clicks
                value = int(32767 * volume * wave * fade)
                for _ in range(self._channels):
                    samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass
