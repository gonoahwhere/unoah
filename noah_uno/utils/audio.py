from contextlib import closing
from time import perf_counter
from wx.adv import Sound
import wave

from .config import AUDIO_DIR

TOLERANCE: float = 0.5
"""The tolerance margin in seconds that allows an audio with a lower priority value to be played over a currently playing audio that has a higher priority value."""

class Audio:
    """A prioritized audio."""

    __slots__: tuple[str, ...] = ('audio', 'priority', 'duration', 'end')

    audio: Sound
    """The audio's wxWidgets sound instance."""

    priority: int
    """The audio's priority value."""

    duration: float
    """The audio's duration in seconds."""

    end: float
    """When the audio can be played over another audio with a lower priority value."""

    def __init__(self, filename: str, priority: int):
        path = str(AUDIO_DIR.joinpath(f'{filename}.wav'))

        self.audio = Sound(path)
        self.priority = priority

        with closing(wave.open(path, 'r')) as wav:
            self.duration = wav.getnframes() / float(wav.getframerate())

        self.end = 0.0

    def play(self) -> None:
        """Plays the audio."""

        self.audio.Play()
        self.end = perf_counter() + self.duration

    @property
    def has_stopped(self) -> bool:
        """Whether the audio has stopped playing."""

        return perf_counter() >= (self.end - TOLERANCE)

class PriorityPlayer:
    """A priority-based audio player."""

    __slots__: tuple[str, ...] = ('audio', 'playing')

    audio: dict[str, Audio]
    """The player's audio mapping."""

    playing: Audio | None
    """The currently playing audio."""

    def __init__(self):
        self.audio = {}
        self.playing = None

    def add(self, filename: str, priority: int) -> None:
        """Registers an audio with a given priority value."""

        self.audio[filename] = Audio(filename, priority)

    def play(self, filename: str) -> None:
        """Tries to play an audio."""

        audio = self.audio[filename]

        if (
            self.playing is None
            or self.playing.has_stopped
            or audio.priority >= self.playing.priority
        ):
            audio.play()

            self.playing = audio