"""Translate parsed Cadence script bodies into ElevenLabs-ready text.

ElevenLabs Multilingual v2 supports SSML <break time="X.0s"/> tags up to 3 seconds.
For pauses longer than 3s but ≤9s, we chain multiple break tags.
For pauses ≥10s, we flag them as "long silences" — the app should handle these
by inserting actual silence between audio chunks, not by relying on TTS-rendered breaks.

Conventions:
- [PAUSE 3s] → <break time="3.0s"/>
- [PAUSE 5s] → <break time="3.0s"/> <break time="2.0s"/>
- [PAUSE 30s+] → renderer raises a warning. For the pilot we still chain breaks
  up to a configurable max; for production these become silence segments.
- [BREATH IN — 4s], [BREATH OUT — 6s] → break tags of the same duration
- [INHALE], [EXHALE] → 2.5s and 3.5s breaks respectively
- [soft], [firmer], [whispered], [warm] → dropped (Multilingual v2 doesn't reliably
  support inline emotion control; we use voice settings + writerly cues for tone)
- (Stage directions in parens at line start) → dropped
- Markdown emphasis (*italics*, _underscore_) → markup stripped, words kept
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .parser import (
    PAUSE_MARKER,
    BREATH_IN_MARKER,
    BREATH_OUT_MARKER,
    INHALE_MARKER,
    EXHALE_MARKER,
    STAGE_DIRECTION,
    TONE_MARKER,
)


@dataclass
class RenderedScript:
    """Result of rendering a script body for TTS."""

    text: str                    # the SSML/plain text to send to ElevenLabs
    char_count: int              # billable characters
    long_pauses: list[int]       # list of pause durations (in seconds) >= 10s
                                 # that the app should handle as silence segments
    warnings: list[str]          # any concerns the renderer surfaced


# Maximum break duration ElevenLabs honors per tag
MAX_BREAK_SECONDS = 3

# Pauses at or above this threshold are flagged as long silences for the app
# to handle separately (rather than chaining 10+ break tags, which produces
# audio artifacts).
LONG_PAUSE_THRESHOLD = 10


def _build_break_chain(seconds: int) -> str:
    """Returns 'duration' worth of break tags, chained at MAX_BREAK_SECONDS each.
    Caller is responsible for deciding whether to chain or to split."""
    if seconds <= 0:
        return ""
    parts: list[str] = []
    remaining = seconds
    while remaining > 0:
        chunk = min(remaining, MAX_BREAK_SECONDS)
        parts.append(f'<break time="{chunk:.1f}s"/>')
        remaining -= chunk
    return " ".join(parts)


def render_for_tts(body_md: str) -> RenderedScript:
    """Turns one session body into ElevenLabs-ready text.

    Returns RenderedScript with the text, char count (for cost estimation),
    long-pause durations to be handled out-of-band, and any warnings."""

    text = body_md
    long_pauses: list[int] = []
    warnings: list[str] = []

    # 1. Drop stage directions like (Audio cues a soft chime...)
    text = STAGE_DIRECTION.sub("", text)

    # 2. Drop tone markers [soft], [firmer], [whispered], [warm]
    text = TONE_MARKER.sub("", text)

    # 3. Replace PAUSE markers with chained break tags or long-pause flags
    def replace_pause(m: re.Match[str]) -> str:
        seconds = int(m.group(1))
        if seconds >= LONG_PAUSE_THRESHOLD:
            long_pauses.append(seconds)
            # Use a max-duration break here as a placeholder; the app should
            # ideally split the audio at this point and insert real silence.
            # For pilot generation we still want SOME pause baked in.
            return _build_break_chain(MAX_BREAK_SECONDS)
        return _build_break_chain(seconds)

    text = PAUSE_MARKER.sub(replace_pause, text)

    # 4. Replace BREATH IN/OUT markers with break tags of the same duration
    def replace_breath(m: re.Match[str]) -> str:
        seconds = int(m.group(1))
        return _build_break_chain(min(seconds, MAX_BREAK_SECONDS))

    text = BREATH_IN_MARKER.sub(replace_breath, text)
    text = BREATH_OUT_MARKER.sub(replace_breath, text)

    # 5. Replace INHALE / EXHALE with shorter breath cues
    text = INHALE_MARKER.sub('<break time="2.5s"/>', text)
    text = EXHALE_MARKER.sub('<break time="3.0s"/>', text)

    # 6. Strip markdown emphasis but keep the words
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # 7. Normalize whitespace — collapse runs of blank lines but keep paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = text.strip()

    # 8. Sanity warnings
    char_count = len(text)
    if char_count > 9500:
        warnings.append(
            f"Rendered text is {char_count} chars — close to v2's 10,000-char limit. "
            "Consider splitting this session at a natural break."
        )

    if long_pauses:
        warnings.append(
            f"Session has {len(long_pauses)} long pause(s) (>{LONG_PAUSE_THRESHOLD}s): "
            f"{long_pauses}. For production, split the audio at these points and "
            "insert actual silence rather than relying on chained break tags."
        )

    # Crude check for excessive break tag density
    break_count = text.count("<break ")
    if break_count > 80:
        warnings.append(
            f"Session has {break_count} break tags. ElevenLabs docs warn that excessive "
            "break tags can cause speed-up artifacts. Listen carefully on first generation."
        )

    return RenderedScript(
        text=text,
        char_count=char_count,
        long_pauses=long_pauses,
        warnings=warnings,
    )


# ------------------------------------------------------------------
# CLI: quick check on a single file
# ------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path

    from .parser import parse_file

    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = Path(__file__).resolve().parent.parent / "content/variant_a_week_1.md"

    jobs = parse_file(target)
    print(f"Rendering {len(jobs)} sessions from {target.name}\n")

    total_chars = 0
    total_warnings = 0
    for job in jobs:
        rendered = render_for_tts(job.body_md)
        total_chars += rendered.char_count
        total_warnings += len(rendered.warnings)
        flag = "⚠ " if rendered.warnings else "  "
        print(f"{flag}{job.session_id():50s} {rendered.char_count:>5d} chars")
        for w in rendered.warnings:
            print(f"     - {w}")

    print()
    print(f"Total: {total_chars} chars, {total_warnings} warnings")
