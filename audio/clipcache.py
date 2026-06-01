"""Persistent on-disk clip cache for the splice pipeline.

Avoids redundant TTS calls for repeated cue words ("Hold.", "Two.", "Out." recur
dozens of times across library sessions) and reuses pre-generated silence files
across sessions. Each unique (rendered_text, voice_id, model_id, settings) tuple
is generated once and stored here; subsequent sessions use the cached file.

An identical cache entry also guarantees audible consistency: the same cue word
sounds identical every time it appears rather than varying across non-deterministic
TTS renders.

Default location: audio_output/.clip_cache/ (gitignored).

Cache key = SHA-256 of the POST-render_for_tts text plus voice/model/settings,
so whitespace normalization and markup stripping are included in the key. Any
change to voice settings or model naturally produces a cache miss.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "audio_output" / ".clip_cache"

# A valid narration clip is at least this large. Clips smaller than this are
# treated as failed TTS responses and not cached.
MIN_CLIP_BYTES = 500


def clip_key(
    rendered_text: str,
    voice_id: str,
    model_id: str,
    settings: dict,
) -> str:
    """Return a stable 64-char hex key for a (text, voice, model, settings) tuple.

    `settings` must have defaults already resolved so the key is deterministic
    regardless of which call site supplied the config."""
    payload = json.dumps(
        {
            "text": rendered_text,
            "voice_id": voice_id,
            "model_id": model_id,
            "settings": settings,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def get_clip(cache_dir: Path, key: str) -> Path | None:
    """Return path to a valid cached narration clip, or None on miss."""
    p = cache_dir / f"{key}.mp3"
    if p.exists() and p.stat().st_size >= MIN_CLIP_BYTES:
        return p
    return None


def put_clip(cache_dir: Path, key: str, source: Path) -> Path:
    """Copy a freshly generated narration clip into the cache.

    Returns the cache path (callers should use this path, not the tmp source)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"{key}.mp3"
    shutil.copy2(source, dest)
    return dest


def get_silence(cache_dir: Path, duration_secs: float) -> Path | None:
    """Return path to a valid cached silence clip, or None on miss."""
    p = cache_dir / f"silence_{duration_secs:g}s.mp3"
    if p.exists() and p.stat().st_size > 0:
        return p
    return None


def put_silence(cache_dir: Path, duration_secs: float, source: Path) -> Path:
    """Copy a freshly generated silence file into the cache.

    Returns the cache path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"silence_{duration_secs:g}s.mp3"
    shutil.copy2(source, dest)
    return dest
