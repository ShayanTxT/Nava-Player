"""Playback engine built on QtMultimedia."""
from __future__ import annotations

import os
import random

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from .library import Track


class PlayerController(QObject):
    track_changed = Signal(object)      # Track | None
    playing_changed = Signal(bool)
    position_changed = Signal(int)      # ms
    duration_changed = Signal(int)      # ms
    volume_changed = Signal(int)
    queue_changed = Signal()
    error = Signal(str)
    status = Signal(str)
    repeat_changed = Signal(str)
    shuffle_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)

        self.queue: list[Track] = []
        self._order: list[int] = []         # playback order -> indices into queue
        self._pos: int = -1
        self._shuffle = False
        self._repeat = "off"                # off | all | one
        self._errors_in_a_row = 0
        self._user_seeking = False

        self._player.positionChanged.connect(
            lambda ms: self.position_changed.emit(int(ms)))
        self._player.durationChanged.connect(self._on_duration)
        self._player.playbackStateChanged.connect(self._on_state)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)

        self._audio.setVolume(0.72)

    # ------------------------------------------------------------------ api
    @property
    def current(self) -> Track | None:
        if 0 <= self._pos < len(self._order):
            index = self._order[self._pos]
            if 0 <= index < len(self.queue):
                return self.queue[index]
        return None

    @property
    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlayingState

    def has_media(self) -> bool:
        return self._player.source().isValid()

    def set_volume(self, value: int):
        value = max(0, min(100, int(value)))
        self._audio.setVolume(value / 100.0)
        self.volume_changed.emit(value)

    def volume(self) -> int:
        return int(round(self._audio.volume() * 100))

    def set_muted(self, muted: bool):
        self._audio.setMuted(bool(muted))

    def is_muted(self) -> bool:
        return self._audio.isMuted()

    # ---------------------------------------------------------------- queue
    def set_queue(self, tracks: list[Track], start_index: int = 0, autoplay: bool = True):
        self.queue = list(tracks)
        self._rebuild_order(start_pos=None)
        self._pos = self._index_to_order(start_index) if self.queue else -1
        self.queue_changed.emit()
        if autoplay and self._pos >= 0:
            self._play_current()
        elif self._pos < 0:
            self._player.stop()
            self._player.setSource(QUrl())
            self.track_changed.emit(None)

    def play_track(self, track: Track, queue: list[Track] | None = None):
        tracks = queue if queue is not None else (self.queue or [track])
        try:
            start = next(i for i, t in enumerate(tracks) if t.path == track.path)
        except StopIteration:
            tracks = list(tracks) + [track]
            start = len(tracks) - 1
        self.set_queue(tracks, start, autoplay=True)

    def _index_to_order(self, index: int) -> int:
        if not self._order:
            return -1
        for order_pos, q_index in enumerate(self._order):
            if q_index == index:
                return order_pos
        return -1

    def _rebuild_order(self, start_pos: int | None = None):
        indices = list(range(len(self.queue)))
        if self._shuffle:
            current = None
            if start_pos is not None and 0 <= start_pos < len(self._order):
                current = self._order[start_pos]
            random.shuffle(indices)
            if current is not None and current in indices:
                indices.remove(current)
                indices.insert(0, current)
        self._order = indices

    # ------------------------------------------------------------ transport
    def _play_current(self):
        track = self.current
        if track is None:
            return
        if not os.path.isfile(track.path):
            self.error.emit(track.path)
            self._errors_in_a_row += 1
            if self._errors_in_a_row < 6:
                self.next(auto=True)
            return
        self._errors_in_a_row = 0
        self._player.setSource(QUrl.fromLocalFile(track.path))
        self._player.play()
        self.track_changed.emit(track)
        self.duration_changed.emit(int(track.duration * 1000))

    def toggle(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        elif self._player.source().isValid():
            self._player.play()
        elif self._pos >= 0:
            self._play_current()

    def play(self):
        if not self.is_playing:
            self.toggle()

    def pause(self):
        if self.is_playing:
            self._player.pause()

    def stop(self):
        self._player.stop()

    def next(self, auto: bool = False):
        if not self._order:
            return
        if self._repeat == "one" and auto and self.current is not None:
            self._player.setPosition(0)
            self._player.play()
            return
        if self._pos + 1 < len(self._order):
            self._pos += 1
        elif self._repeat == "all":
            self._pos = 0
            if self._shuffle:
                self._rebuild_order()
        else:
            self._player.stop()
            self._player.setPosition(0)
            self.playing_changed.emit(False)
            return
        self._play_current()

    def prev(self):
        if not self._order:
            return
        # restart the song if we're more than 4s in
        if self._player.position() > 4000 and self.current is not None:
            self._player.setPosition(0)
            return
        if self._pos - 1 >= 0:
            self._pos -= 1
        elif self._repeat == "all":
            self._pos = len(self._order) - 1
        else:
            self._player.setPosition(0)
            return
        self._play_current()

    def set_position(self, ms: int):
        self._user_seeking = True
        self._player.setPosition(int(ms))
        self._user_seeking = False

    def position(self) -> int:
        return self._player.position()

    def duration(self) -> int:
        return self._player.duration()

    # ---------------------------------------------------------------- modes
    def set_shuffle(self, enabled: bool):
        if enabled == self._shuffle:
            return
        self._shuffle = bool(enabled)
        current_track = self.current
        self._rebuild_order(start_pos=self._pos)
        if current_track is not None:
            try:
                new_index = self.queue.index(current_track)
                self._pos = self._index_to_order(new_index)
            except ValueError:
                pass
        self.shuffle_changed.emit(self._shuffle)

    def shuffle(self) -> bool:
        return self._shuffle

    def set_repeat(self, mode: str):
        self._repeat = mode if mode in ("off", "all", "one") else "off"
        self.repeat_changed.emit(self._repeat)

    def cycle_repeat(self) -> str:
        order = ["off", "all", "one"]
        self.set_repeat(order[(order.index(self._repeat) + 1) % 3])
        return self._repeat

    def repeat(self) -> str:
        return self._repeat

    # --------------------------------------------------------------- signals
    def _on_duration(self, ms: int):
        self.duration_changed.emit(ms)

    def _on_state(self, state):
        self.playing_changed.emit(state == QMediaPlayer.PlayingState)

    def _on_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self._errors_in_a_row = 0
            self.next(auto=True)

    def _on_error(self, err, message: str):
        if err == QMediaPlayer.NoError:
            return
        track = self.current
        self.error.emit(message or (track.path if track else ""))
        self._errors_in_a_row += 1
        if self._errors_in_a_row <= 5:
            self.next(auto=True)
        else:
            self.status.emit("many-errors")
