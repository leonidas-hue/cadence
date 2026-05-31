"""Background "soothing melody" for guided Cadence sessions.

Two ways to deliver the user-facing toggle:

PRODUCTION (recommended): app-side mixing.
    Ship ONE narration MP3 per session plus ONE loopable ambient bed asset.
    In Flutter (just_audio), play two players simultaneously: the narration
    once, and the bed on LoopMode.all at ~12-18% volume underneath. The "tick
    a melody" checkbox just starts/stops the second player. Benefits:
      - true runtime toggle, no doubled storage
      - one bed serves every guided session, looped to any length
      - the bed naturally fills the spliced silence beats (no dead air during
        the self-paced breathing blocks)
      - you can add a volume slider for free
    This module is NOT needed for that path.

PILOT (this module): bake with-music previews so you can judge the vibe and the
    volume level before building Flutter. Mixes a finished narration MP3 with a
    looped, low-volume, faded ambient bed via ffmpeg, cut to the narration's
    exact length.

Requires: ffmpeg (brew install ffmpeg).

Choosing a bed: use a licensed, *seamlessly looping* ambient track — a key-neutral
pad or drone with no melodic hook that competes with the voice. 60-120 s is plenty
(it loops). Pre-normalize it quiet. Sources: licensed stock libraries, or generate
one and loop-edit it. Do NOT ship copyrighted music.

Usage:
    from audio.music import add_background_music
    add_background_music("a_1_5_box-breathing_adam.mp3", "beds/calm_pad.mp3",
                         "a_1_5_box-breathing_adam_music.mp3")

    # or batch a directory of guided-session MP3s:
    python -m audio.music --bed beds/calm_pad.mp3 --in audio_output/pilot --out audio_output/pilot_music
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Optional

# Sits the bed well under a calm voice. 0.10-0.18 is the usable range; 0.12 is a
# good default for a quiet pad. Tune by ear on the first preview.
DEFAULT_MUSIC_VOLUME = 0.12
DEFAULT_FADE_SECS = 2.0
_BIT_RATE = "128k"
_SAMPLE_RATE = 44100


def _probe_duration(path: Path) -> float:
    """Return audio duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"ffprobe failed on {path}: {result.stderr[-300:]}")
    return float(result.stdout.strip())


def add_background_music(
    narration_path: str | Path,
    bed_path: str | Path,
    output_path: str | Path,
    *,
    music_volume: float = DEFAULT_MUSIC_VOLUME,
    fade_secs: float = DEFAULT_FADE_SECS,
) -> Path:
    """Overlay a looped, low-volume, faded ambient bed under a narration MP3.

    The bed is looped with -stream_loop (memory-safe), volume-reduced, faded in
    at the start and out at the end, then mixed and cut to the narration length.
    Returns the output path.
    """
    narration_path = Path(narration_path)
    bed_path = Path(bed_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dur = _probe_duration(narration_path)
    fade = min(fade_secs, dur / 2.0)
    out_st = max(0.0, dur - fade)

    filt = (
        f"[1:a]volume={music_volume},"
        f"afade=t=in:st=0:d={fade:.3f},"
        f"afade=t=out:st={out_st:.3f}:d={fade:.3f}[bed];"
        f"[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0[mix]"
    )

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(narration_path),       # input 0: narration (sets length)
            "-stream_loop", "-1",
            "-i", str(bed_path),             # input 1: bed, looped infinitely
            "-filter_complex", filt,
            "-map", "[mix]",
            "-acodec", "libmp3lame",
            "-ab", _BIT_RATE,
            "-ar", str(_SAMPLE_RATE),
            str(output_path),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mix failed: {result.stderr[-400:]}")
    return output_path


def _is_guided(mp3_path: Path) -> bool:
    """Heuristic: a guided session has a self-paced/breath block, which the
    splicer would have produced. We can't read markers from an MP3, so this
    mixer treats whatever you point --in at as the guided set. Keep your guided
    output in its own folder, or pass explicit files."""
    return mp3_path.suffix.lower() == ".mp3" and not mp3_path.stem.endswith("_music")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bed", required=True, help="path to the looping ambient bed MP3")
    ap.add_argument("--in", dest="in_dir", required=True, help="dir of narration MP3s")
    ap.add_argument("--out", dest="out_dir", required=True, help="dir for mixed MP3s")
    ap.add_argument("--volume", type=float, default=DEFAULT_MUSIC_VOLUME)
    ap.add_argument("--fade", type=float, default=DEFAULT_FADE_SECS)
    args = ap.parse_args()

    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    files = sorted(p for p in in_dir.iterdir() if _is_guided(p))
    if not files:
        print(f"No narration MP3s found in {in_dir}")
        return

    print(f"Mixing {len(files)} files with bed {Path(args.bed).name} "
          f"@ volume {args.volume}\n")
    for p in files:
        out = out_dir / f"{p.stem}_music.mp3"
        try:
            add_background_music(p, args.bed, out,
                                 music_volume=args.volume, fade_secs=args.fade)
            print(f"  ✓ {out.name}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {p.name}: {e}")

    print(f"\nDone. Previews in {out_dir}")


if __name__ == "__main__":
    main()
