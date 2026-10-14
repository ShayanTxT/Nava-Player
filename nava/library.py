"""Music library: scanning folders, reading tags, extracting cover art."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

AUDIO_EXTS = {
    ".mp3", ".m4a", ".m4b", ".mp4", ".aac", ".flac", ".wav", ".wave",
    ".ogg", ".oga", ".opus", ".wma", ".aiff", ".aif", ".ape", ".wv", ".mka",
}

COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png", "folder.jpg", "folder.jpeg",
               "front.jpg", "album.jpg", "albumart.jpg", "artwork.jpg", "cover.webp")


def is_audio(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in AUDIO_EXTS


@dataclass
class Track:
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    track_no: int = 0
    source: str = ""          # the root folder this track came from
    _cover: bytes | None = field(default=None, repr=False)
    _cover_done: bool = field(default=False, repr=False)

    @property
    def name(self) -> str:
        return os.path.splitext(os.path.basename(self.path))[0]

    @property
    def display_title(self) -> str:
        return self.title or self.name

    @property
    def ext(self) -> str:
        return os.path.splitext(self.path)[1].lower()

    @property
    def duration_text(self) -> str:
        secs = int(round(self.duration or 0))
        if secs <= 0:
            return "--:--"
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def key(self) -> str:
        return os.path.normcase(self.path)


def _clean(value, fallback=""):
    if isinstance(value, list):
        value = " / ".join(str(v) for v in value) if value else ""
    if value is None:
        return fallback
    value = str(value).strip()
    return value or fallback


def read_tags(path: str) -> Track:
    """Read metadata with mutagen; never raises."""
    track = Track(path=path)
    try:
        from mutagen import File as MutaFile
        audio = MutaFile(path, easy=True)
        if audio is not None:
            tags = audio.tags or {}

            def get(*keys):
                for k in keys:
                    try:
                        if k in tags:
                            v = tags[k]
                        else:
                            v = None
                        if isinstance(v, list):
                            v = v[0] if v else None
                        if v:
                            return str(v)
                    except Exception:
                        continue
                return ""

            track.title = get("title", "tit2", "\xa9nam")
            track.artist = get("artist", "albumartist", "tp1", "\xa9ART", "aART")
            track.album = get("album", "talb", "\xa9alb")
            tn = get("tracknumber", "trkn")
            if tn:
                try:
                    track.track_no = int(str(tn).split("/")[0])
                except Exception:
                    track.track_no = 0
            try:
                if audio.info is not None:
                    track.duration = float(getattr(audio.info, "length", 0.0) or 0.0)
            except Exception:
                pass
    except Exception:
        pass
    return track


def extract_cover(path: str) -> bytes | None:
    """Return raw image bytes of embedded cover, else a cover.jpg next to the file."""
    try:
        from mutagen import File as MutaFile
        audio = MutaFile(path)
        tags = getattr(audio, "tags", None)
        if tags is not None:
            # ID3 (mp3 / wav / aiff)
            try:
                pics = tags.getall("APIC")
                if pics:
                    return bytes(pics[0].data)
            except Exception:
                pass
            # FLAC / Ogg pictures
            try:
                pics = getattr(tags, "pictures", None)
                if pics:
                    return bytes(pics[0].data)
            except Exception:
                pass
            # MP4
            try:
                covr = tags.get("covr")
                if covr:
                    return bytes(covr[0])
            except Exception:
                pass
            # ASF / WMA
            try:
                pic = tags.get("WM/Picture")
                if pic:
                    val = pic[0] if isinstance(pic, list) else pic
                    return bytes(val.value if hasattr(val, "value") else val)
            except Exception:
                pass
            # Vorbis comment base64 picture
            try:
                import base64
                import struct
                raw = tags.get("metadata_block_picture")
                if raw:
                    data = base64.b64decode(raw[0])
                    pos = 0
                    for _ in range(3):                      # mime, desc, width/height/depth/colors
                        ln = struct.unpack(">i", data[pos:pos + 4])[0]
                        pos += 4 + ln
                    ln = struct.unpack(">i", data[pos:pos + 4])[0]
                    return data[pos + 4:pos + 4 + ln]
            except Exception:
                pass
    except Exception:
        pass

    folder = os.path.dirname(path)
    for name in COVER_NAMES:
        candidate = os.path.join(folder, name)
        if os.path.isfile(candidate):
            try:
                with open(candidate, "rb") as fh:
                    return fh.read()
            except Exception:
                pass
    return None


def scan_folder(root: str, recursive: bool = True, batch_size: int = 60,
                should_stop=None, on_batch=None) -> int:
    """Walk `root`, read tags, stream results through `on_batch`.

    Returns the number of tracks found.  Runs inside a worker thread.
    """
    total = 0
    batch: list[Track] = []
    roots = [root]

    def walk():
        for base in roots:
            if recursive:
                for dirpath, dirnames, filenames in os.walk(base):
                    dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
                    for fn in sorted(filenames):
                        if should_stop and should_stop():
                            return
                        if is_audio(fn):
                            yield os.path.join(dirpath, fn)
            else:
                for fn in sorted(os.listdir(base)):
                    if should_stop and should_stop():
                        return
                    full = os.path.join(base, fn)
                    if os.path.isfile(full) and is_audio(fn):
                        yield full

    for path in walk():
        track = read_tags(path)
        batch.append(track)
        total += 1
        if len(batch) >= batch_size:
            if on_batch:
                on_batch(batch)
            batch = []
    if batch and on_batch:
        on_batch(batch)
    return total


def sort_tracks(tracks: list[Track]) -> list[Track]:
    def key(t: Track):
        folder = os.path.dirname(t.path).lower()
        album = (t.album or "").lower()
        no = t.track_no or 0
        return (folder, album, (no if no else 10 ** 6), (t.display_title or "").lower())

    return sorted(tracks, key=key)
