"""
core/segmenter.py
Splits a stream of per-frame landmarks into per-word chunks using
hands-absent pauses. Knows nothing about the ML model.
"""
from dataclasses import dataclass
from typing import List, Optional, Callable

PAUSE_S = 1.0          # seconds of no-hands that ends a word
MIN_WORD_FRAMES = 5    # shorter -> ignored as noise


@dataclass
class Frame:
    t: float
    landmarks: Optional[object]   # raw (2, 21, 3) array, or None if no hands
    hands_present: bool


@dataclass
class WordChunk:
    frames: List[Frame]
    start_t: float
    end_t: float

    @property
    def n_frames(self) -> int:
        return len(self.frames)


def segment_recording(frames: List[Frame], pause_s: float = PAUSE_S,
                       min_word_frames: int = MIN_WORD_FRAMES) -> List[WordChunk]:
    """Batch mode: splits a full recording (e.g. from a phone upload) into words."""
    chunks, current, pause_start = [], [], None
    for f in frames:
        if f.hands_present:
            current.append(f)
            pause_start = None
        else:
            if current:
                if pause_start is None:
                    pause_start = f.t
                elif f.t - pause_start >= pause_s:
                    if len(current) >= min_word_frames:
                        chunks.append(WordChunk(current, current[0].t, current[-1].t))
                    current, pause_start = [], None
    if current and len(current) >= min_word_frames:
        chunks.append(WordChunk(current, current[0].t, current[-1].t))
    return chunks


class StreamingSegmenter:
    """Frame-by-frame mode for live_demo.py (webcam) and a future WebSocket."""

    def __init__(self, on_word: Callable[[WordChunk], None],
                 pause_s: float = PAUSE_S, min_word_frames: int = MIN_WORD_FRAMES):
        self.on_word = on_word
        self.pause_s = pause_s
        self.min_word_frames = min_word_frames
        self._current: List[Frame] = []
        self._pause_start: Optional[float] = None

    def push(self, frame: Frame) -> None:
        if frame.hands_present:
            self._current.append(frame)
            self._pause_start = None
        else:
            if self._current:
                if self._pause_start is None:
                    self._pause_start = frame.t
                elif frame.t - self._pause_start >= self.pause_s:
                    self._emit()

    def finish(self) -> None:
        self._emit()

    def _emit(self) -> None:
        if self._current and len(self._current) >= self.min_word_frames:
            self.on_word(WordChunk(self._current, self._current[0].t, self._current[-1].t))
        self._current, self._pause_start = [], None