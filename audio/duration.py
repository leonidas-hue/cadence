"""Estimate true playback duration for every Cadence session.

Why this exists
---------------
`render.py`'s `char_count` only measures *billable characters* — it tells you
nothing about how long a session actually PLAYS, because the silence beats
([PAUSE], [BREATH], [HOLD]) contribute most of the runtime in practice sessions
and contribute ZERO characters.

Worse: the current pipeline silently truncates long pauses. A `[PAUSE 120s]`
self-practice block renders as a single 3-second break (see render.replace_pause:
long pauses are flagged but emitted as one MAX_BREAK_SECONDS tag). So a session
written to run 8 minutes can come out under 5.

This module reports, per session and in aggregate:
  - estimated SPEECH time (words / WPM)
  - INTENDED non-speech time  (every marker at its scripted duration)
  - CURRENT non-speech time   (what the pipeline actually emits today)
  - the gap between them       (silence lost to truncation)

Run it before and after the long-pause fix to confirm the fix worked.

Usage:
    python -m audio.duration                 # all content, default 140 wpm
    python -m audio.duration --wpm 130        # slower coach voice
    python -m audio.duration --target 6       # flag sessions >2 min off 6:00
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .parser import (
    parse_content_dir,
    AudioJob,
    PAUSE_MARKER,
    HOLD_MARKER,
    BREATH_IN_MARKER,
    BREATH_OUT_MARKER,
    INHALE_MARKER,
    EXHALE_MARKER,
    strip_speakable_markers,
)
from .render import MAX_BREAK_SECONDS, LONG_PAUSE_THRESHOLD

# INHALE/EXHALE fixed durations must match render.py / splice.py
_INHALE_SECS = 2.5
_EXHALE_SECS = 3.0

# Default narration pace. Calm coach narration runs slower than conversational
# speech (~150 wpm). 140 is a reasonable default for ElevenLabs at stability 0.55;
# drop to ~130 if you set a slower style or use prosody rate control on another
# engine. This is the single biggest lever on the speech-time estimate, so treat
# the numbers as ±10% and trust your ears on the pilot.
_DEFAULT_WPM = 140


@dataclass
class DurationEstimate:
    session_id: str
    words: int
    speech_secs: float
    intended_pause_secs: float
    current_pause_secs: float

    @property
    def intended_total(self) -> float:
        return self.speech_secs + self.intended_pause_secs

    @property
    def current_total(self) -> float:
        return self.speech_secs + self.current_pause_secs

    @property
    def lost_secs(self) -> float:
        return self.intended_pause_secs - self.current_pause_secs


def _intended_pause_secs(body: str) -> float:
    """Sum of all non-speech beats at the duration the SCRIPT specifies."""
    total = 0.0
    for m in PAUSE_MARKER.finditer(body):
        total += int(m.group(1))
    for m in HOLD_MARKER.finditer(body):
        total += int(m.group(1))
    for m in BREATH_IN_MARKER.finditer(body):
        total += int(m.group(1))
    for m in BREATH_OUT_MARKER.finditer(body):
        total += int(m.group(1))
    total += len(INHALE_MARKER.findall(body)) * _INHALE_SECS
    total += len(EXHALE_MARKER.findall(body)) * _EXHALE_SECS
    return total


def _current_pause_secs(body: str) -> float:
    """Sum of non-speech beats as the CURRENT pipeline actually emits them.

    Mirrors render.py + splice.py behaviour (post-Phase-1 fixes):
      - BREATH IN/OUT/INHALE/EXHALE  -> real spliced silence, full duration
      - HOLD                          -> real spliced silence, full duration
      - PAUSE < LONG_PAUSE_THRESHOLD  -> capped break tag, min(x, MAX_BREAK)
      - PAUSE >= LONG_PAUSE_THRESHOLD -> real spliced silence, full duration
    """
    total = 0.0
    for m in PAUSE_MARKER.finditer(body):
        s = int(m.group(1))
        total += s if s >= LONG_PAUSE_THRESHOLD else min(s, MAX_BREAK_SECONDS)
    for m in HOLD_MARKER.finditer(body):
        total += int(m.group(1))
    for m in BREATH_IN_MARKER.finditer(body):
        total += int(m.group(1))
    for m in BREATH_OUT_MARKER.finditer(body):
        total += int(m.group(1))
    total += len(INHALE_MARKER.findall(body)) * _INHALE_SECS
    total += len(EXHALE_MARKER.findall(body)) * _EXHALE_SECS
    return total


def estimate(job: AudioJob, wpm: int = _DEFAULT_WPM) -> DurationEstimate:
    spoken = strip_speakable_markers(job.body_md)
    # Drop the inline duration markers too, so they don't count as words.
    for mk in (PAUSE_MARKER, HOLD_MARKER, BREATH_IN_MARKER,
               BREATH_OUT_MARKER, INHALE_MARKER, EXHALE_MARKER):
        spoken = mk.sub("", spoken)
    words = len(spoken.split())
    speech_secs = words / wpm * 60.0
    return DurationEstimate(
        session_id=job.session_id(),
        words=words,
        speech_secs=speech_secs,
        intended_pause_secs=_intended_pause_secs(job.body_md),
        current_pause_secs=_current_pause_secs(job.body_md),
    )


def _fmt(secs: float) -> str:
    m, s = divmod(int(round(secs)), 60)
    return f"{m:d}:{s:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wpm", type=int, default=_DEFAULT_WPM,
                    help=f"narration words-per-minute (default {_DEFAULT_WPM})")
    ap.add_argument("--target", type=float, default=None,
                    help="target minutes; flag sessions >2 min off target (intended)")
    ap.add_argument("--content", default=None, help="content dir (default ../content)")
    args = ap.parse_args()

    content_dir = Path(args.content) if args.content else (
        Path(__file__).resolve().parent.parent / "content"
    )
    jobs = parse_content_dir(content_dir)

    ests = [estimate(j, wpm=args.wpm) for j in jobs]

    print(f"Duration estimates @ {args.wpm} wpm  ({len(ests)} sessions)\n")
    print(f"{'session':46s} {'intended':>8s} {'current':>8s} {'lost':>7s}")
    print("-" * 74)

    worst = sorted(ests, key=lambda e: e.lost_secs, reverse=True)
    total_intended = total_current = 0.0
    flagged_short = []
    for e in ests:
        total_intended += e.intended_total
        total_current += e.current_total
        flag = " ⚠" if e.lost_secs >= 10 else "  "
        # only print the worst offenders in full to keep output readable
        if e.lost_secs >= 10:
            print(f"{e.session_id:46s} {_fmt(e.intended_total):>8s} "
                  f"{_fmt(e.current_total):>8s} {_fmt(e.lost_secs):>7s}{flag}")
        if args.target is not None and abs(e.intended_total - args.target * 60) > 120:
            flagged_short.append(e)

    print("-" * 74)
    print(f"{'TOTAL':46s} {_fmt(total_intended):>8s} {_fmt(total_current):>8s} "
          f"{_fmt(total_intended - total_current):>7s}")
    print()
    print(f"Sessions losing >=10s of silence to truncation: "
          f"{sum(1 for e in ests if e.lost_secs >= 10)}")
    print(f"Total silence lost across library: {_fmt(total_intended - total_current)} "
          f"({(total_intended - total_current)/60:.1f} min)")

    if args.target is not None and flagged_short:
        print(f"\nSessions >2 min off the {args.target:.0f}:00 target (by intended runtime):")
        for e in sorted(flagged_short, key=lambda e: e.intended_total):
            print(f"  {e.session_id:46s} {_fmt(e.intended_total)}")


if __name__ == "__main__":
    main()
