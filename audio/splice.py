"""Silence-splicing pipeline for guided practice sessions.

ElevenLabs v2 cannot reliably render guided breathing with long silence beats
between single-word cues — the model compresses/speeds up the audio. This module
splits the session body at BREATH markers, generates TTS for each narration
chunk, generates real silence for each breath beat via ffmpeg, then concatenates
everything into a single MP3.

Requires: ffmpeg (brew install ffmpeg)
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import tempfile

import re

from .parser import (
    BREATH_IN_MARKER, BREATH_OUT_MARKER, INHALE_MARKER, EXHALE_MARKER,
    PAUSE_MARKER, HOLD_MARKER,
)
from .render import render_for_tts, LONG_PAUSE_THRESHOLD

# Matches a standalone [PAUSE Ns] line (entire line, stripped).
# Whether it becomes a SilenceSegment or an inline <break> tag is decided
# by _prev_structural / _next_structural in split_for_splicing().
_ANY_PAUSE_LINE = re.compile(r"^\[PAUSE\s+(\d+)s\]$", re.IGNORECASE)

# Exhaustive set of tokens that may appear in action-cue lines.  A line is an
# action cue iff EVERY content token (after stripping punctuation) is in this set.
# Short prose sentences like "Quick context." or "Good work." contain non-cue
# words and are correctly treated as prose — no word-count heuristic needed.
_CUE_WORDS = frozenset({
    'in', 'out', 'inhale', 'exhale', 'hold', 'breathe',
    'and', 'again', 'begin', 'release', 'contract',
    'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
})

_TOKEN_SPLIT = re.compile(r'[^\w]+')  # split on any run of non-word characters


def _is_action_cue(s: str) -> bool:
    """True if every content token of s is a known cue-vocabulary word."""
    tokens = [t for t in _TOKEN_SPLIT.split(s.lower()) if t]
    return bool(tokens) and all(t in _CUE_WORDS for t in tokens)


def _is_structural(s: str) -> bool:
    """True if line s is an unambiguous structural beat for splice decisions.

    Structural: breath/hold/pause markers, or a line whose every content token
    is in the cue vocabulary (action cues like 'Two.', 'Breathe in.', 'Hold.',
    'Contract.').  Short prose statements like 'Quick context.' or 'Good work.'
    contain non-cue words and are correctly classified as prose.
    """
    if not s:
        return False
    if (BREATH_IN_MARKER.match(s) or BREATH_OUT_MARKER.match(s) or
            HOLD_MARKER.match(s) or INHALE_MARKER.match(s) or EXHALE_MARKER.match(s) or
            _ANY_PAUSE_LINE.match(s)):
        return True
    return _is_action_cue(s)


def _prev_structural(current_lines: list[str]) -> bool:
    """True if the nearest preceding non-blank, non-directive line is structural."""
    for line in reversed(current_lines):
        s = line.strip()
        if not s:
            continue
        if _is_structural(s):
            return True
        if s.startswith('[') and s.endswith(']'):
            continue  # bracket directive (e.g. [firmer]) — skip
        return False
    return False


def _next_structural(all_lines: list[str], idx: int) -> bool:
    """True if the nearest following non-blank, non-directive line is structural."""
    for j in range(idx + 1, len(all_lines)):
        s = all_lines[j].strip()
        if not s:
            continue
        if _is_structural(s):
            return True
        if s.startswith('[') and s.endswith(']'):
            continue  # bracket directive — skip
        return False
    return False

# Must match ElevenLabs output format (mp3_44100_128)
_SAMPLE_RATE = 44100
_BIT_RATE = "128k"


@dataclass
class NarrationSegment:
    text: str  # raw markdown — rendered by render_for_tts before each TTS call


@dataclass
class SilenceSegment:
    duration_secs: float
    label: str = ""


Segment = Union[NarrationSegment, SilenceSegment]


def needs_splicing(body_md: str) -> bool:
    """True if this session needs the splice pipeline: guided breathing OR
    any pause long enough that a 3s break tag would be a meaningless substitute."""
    if (
        BREATH_IN_MARKER.search(body_md)
        or BREATH_OUT_MARKER.search(body_md)
        or INHALE_MARKER.search(body_md)
        or EXHALE_MARKER.search(body_md)
        or HOLD_MARKER.search(body_md)
    ):
        return True
    for m in PAUSE_MARKER.finditer(body_md):
        if int(m.group(1)) >= LONG_PAUSE_THRESHOLD:
            return True
    return False


def split_for_splicing(body_md: str) -> list[Segment]:
    """Split a script body at BREATH markers into narration and silence segments.

    Each [BREATH IN — Xs] / [BREATH OUT — Xs] / [INHALE] / [EXHALE] becomes a
    SilenceSegment. All surrounding text (cue words, regular pauses, narration)
    stays as NarrationSegment and is rendered via render_for_tts.

    Post-processing removes empty narration segments and merges adjacent silences.
    """
    segments: list[Segment] = []
    current_lines: list[str] = []

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        if text:
            segments.append(NarrationSegment(text))
        current_lines.clear()

    all_lines = body_md.splitlines()
    for i, line in enumerate(all_lines):
        s = line.strip()

        m = _ANY_PAUSE_LINE.match(s)
        if m:
            n = int(m.group(1))
            if n >= 4:
                # 4s+ is always a structural exercise beat — real silence,
                # never an inline break tag (which ElevenLabs caps at 3s).
                flush()
                segments.append(SilenceSegment(float(n), f"pause {n}s"))
                continue
            # Short pauses (1–3s): splice only when adjacent to a structural
            # beat (cue word, breath marker, or another pause).  Short prose
            # pacing stays inline as <break> tags.
            if _prev_structural(current_lines) or _next_structural(all_lines, i):
                flush()
                segments.append(SilenceSegment(float(n), f"pause {n}s"))
                continue
            # Prose context — leave pause as inline break tag via render_for_tts

        m = HOLD_MARKER.match(s)
        if m:
            flush()
            segments.append(SilenceSegment(float(m.group(1)), f"hold {m.group(1)}s"))
            continue

        m = BREATH_IN_MARKER.match(s)
        if m:
            flush()
            segments.append(SilenceSegment(float(m.group(1)), f"inhale {m.group(1)}s"))
            continue

        m = BREATH_OUT_MARKER.match(s)
        if m:
            flush()
            segments.append(SilenceSegment(float(m.group(1)), f"exhale {m.group(1)}s"))
            continue

        if INHALE_MARKER.match(s):
            flush()
            segments.append(SilenceSegment(2.5, "inhale"))
            continue

        if EXHALE_MARKER.match(s):
            flush()
            segments.append(SilenceSegment(3.0, "exhale"))
            continue

        current_lines.append(line)

    flush()

    # Post-process: drop empty narration; merge adjacent silences
    merged: list[Segment] = []
    for seg in segments:
        if isinstance(seg, NarrationSegment):
            if not render_for_tts(seg.text).text.strip():
                continue
        if (
            isinstance(seg, SilenceSegment)
            and merged
            and isinstance(merged[-1], SilenceSegment)
        ):
            prev = merged[-1]
            merged[-1] = SilenceSegment(
                prev.duration_secs + seg.duration_secs,
                f"{prev.label}+{seg.label}",
            )
        else:
            merged.append(seg)

    return merged


def _make_silence(duration_secs: float, output_path: Path) -> None:
    """Write a silent MP3 of the given duration using ffmpeg."""
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r={_SAMPLE_RATE}:cl=mono",
            "-t", str(duration_secs),
            "-acodec", "libmp3lame",
            "-ab", _BIT_RATE,
            "-ar", str(_SAMPLE_RATE),
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg silence failed: {result.stderr[-400:]}")


def _concat(segment_files: list[Path], output_path: Path) -> None:
    """Concatenate MP3 files into one via ffmpeg concat demuxer with re-encode."""
    list_path = output_path.with_suffix(".concat_list.txt")
    try:
        list_path.write_text(
            "\n".join(f"file '{p.resolve()}'" for p in segment_files) + "\n"
        )
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_path),
                "-acodec", "libmp3lame",
                "-ab", _BIT_RATE,
                "-ar", str(_SAMPLE_RATE),
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {result.stderr[-400:]}")
    finally:
        list_path.unlink(missing_ok=True)


def generate_spliced(
    *,
    client,
    job,
    voice_name: str,
    voice_config: dict,
    output_path: Path,
    model_id: str,
    output_format: str,
    max_retries: int = 3,
    use_cache: bool = True,
    cache_dir: Optional[Path] = None,
) -> tuple[bool, Optional[str]]:
    """Generate a spliced session: TTS segments interleaved with real silence.

    Returns (success, error_message).
    """
    from .clipcache import (
        clip_key,
        get_clip, put_clip,
        get_silence as cache_get_silence,
        put_silence as cache_put_silence,
        DEFAULT_CACHE_DIR,
    )

    segments = split_for_splicing(job.body_md)

    narr_count = sum(1 for s in segments if isinstance(s, NarrationSegment))
    sil_count = sum(1 for s in segments if isinstance(s, SilenceSegment))
    print(f"     spliced: {narr_count} narration + {sil_count} silence segments")

    voice_id = voice_config["voice_id"]
    raw_settings = voice_config.get("settings", {})
    # Resolve defaults once — used for both the TTS call and the cache key so
    # the key is stable regardless of which config supplied the defaults.
    resolved_settings = {
        "stability": raw_settings.get("stability", 0.55),
        "similarity_boost": raw_settings.get("similarity_boost", 0.75),
        "style": raw_settings.get("style", 0.15),
        "use_speaker_boost": raw_settings.get("use_speaker_boost", True),
        "speed": raw_settings.get("speed", 1.0),
    }

    effective_cache_dir = (cache_dir or DEFAULT_CACHE_DIR) if use_cache else None

    with tempfile.TemporaryDirectory(prefix="cadence_splice_") as tmp:
        tmp_dir = Path(tmp)
        # In-memory dedup for silences within this session (used when cache is off)
        session_silence: dict[float, Path] = {}
        segment_files: list[Path] = []
        cache_hits = 0
        cache_misses = 0

        for i, seg in enumerate(segments):
            if isinstance(seg, SilenceSegment):
                dur = seg.duration_secs

                if use_cache:
                    cached = cache_get_silence(effective_cache_dir, dur)
                    if cached:
                        segment_files.append(cached)
                        cache_hits += 1
                        continue
                    # Miss: generate to tmp, store in persistent cache
                    sil_tmp = tmp_dir / f"silence_tmp_{dur}s.mp3"
                    _make_silence(dur, sil_tmp)
                    cached = cache_put_silence(effective_cache_dir, dur, sil_tmp)
                    segment_files.append(cached)
                    cache_misses += 1
                else:
                    if dur not in session_silence:
                        sil_path = tmp_dir / f"silence_{dur}s.mp3"
                        _make_silence(dur, sil_path)
                        session_silence[dur] = sil_path
                    segment_files.append(session_silence[dur])

            else:  # NarrationSegment
                rendered = render_for_tts(seg.text)
                seg_path = tmp_dir / f"seg_{i:03d}.mp3"

                if use_cache:
                    key = clip_key(rendered.text, voice_id, model_id, resolved_settings)
                    cached = get_clip(effective_cache_dir, key)
                    if cached:
                        segment_files.append(cached)
                        cache_hits += 1
                        continue
                    cache_misses += 1

                last_error: Optional[str] = None
                for attempt in range(max_retries):
                    try:
                        audio = client.text_to_speech.convert(
                            text=rendered.text,
                            voice_id=voice_id,
                            model_id=model_id,
                            output_format=output_format,
                            voice_settings=resolved_settings,
                        )
                        with open(seg_path, "wb") as f:
                            if hasattr(audio, "__iter__") and not isinstance(
                                audio, (bytes, bytearray)
                            ):
                                for chunk in audio:
                                    f.write(chunk)
                            else:
                                f.write(audio)

                        if seg_path.stat().st_size < 500:
                            last_error = (
                                f"seg {i} too small "
                                f"({seg_path.stat().st_size} bytes)"
                            )
                            seg_path.unlink(missing_ok=True)
                            if attempt < max_retries - 1:
                                time.sleep(2 ** attempt)
                            continue

                        last_error = None
                        break

                    except Exception as e:
                        last_error = f"{type(e).__name__}: {e}"
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)

                if last_error:
                    return False, f"seg {i} failed after {max_retries} attempts: {last_error}"

                if use_cache:
                    cached = put_clip(effective_cache_dir, key, seg_path)
                    segment_files.append(cached)
                else:
                    segment_files.append(seg_path)

        if use_cache and (cache_hits + cache_misses) > 0:
            total = cache_hits + cache_misses
            print(f"     cache: {cache_hits}/{total} hits ({cache_hits * 100 // total}%)")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            _concat(segment_files, output_path)
        except Exception as e:
            return False, f"concat failed: {e}"

        MIN_VALID_BYTES = 10_000
        size = output_path.stat().st_size
        if size < MIN_VALID_BYTES:
            output_path.unlink(missing_ok=True)
            return False, f"output too small ({size} bytes); likely concat error"

        return True, None
