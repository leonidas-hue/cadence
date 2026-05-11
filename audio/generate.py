"""Generate audio for AudioJobs using the ElevenLabs API.

Requires:
    pip install elevenlabs python-dotenv
    export ELEVENLABS_API_KEY=sk-xxxxx   (or put in .env at repo root)

Usage:
    # Generate the pilot (one week of one variant, both voices):
    python -m audio.pilot

    # Or generate a custom subset via the library:
    from audio.parser import parse_content_dir
    from audio.generate import generate_jobs
    jobs = parse_content_dir("content")
    pilot_jobs = [j for j in jobs if j.variant == "a" and j.week == 1]
    generate_jobs(pilot_jobs, output_dir="audio/pilot_output")
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable, Optional

from .parser import AudioJob
from .render import render_for_tts


# Load .env from repo root if present, so ELEVENLABS_API_KEY can live in a file
# rather than being exported every shell session.
try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(_repo_root / ".env")
except ImportError:
    # python-dotenv not installed — caller can still export the env var manually
    pass


# Defaults — override via env or generate_jobs() args
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"  # 44.1kHz mono 128kbps as committed in spec
DEFAULT_VOICES_JSON = Path(__file__).resolve().parent.parent / "voices.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "audio_output"

# Conservative rate limit. ElevenLabs allows higher on most plans, but for
# overnight production runs we'd rather spread load than risk 429s.
DELAY_BETWEEN_CALLS = 0.5  # seconds


def load_voices() -> dict:
    """Returns the parsed voices.json: {voices: {adam: {voice_id, settings}, bella: {...}}}"""
    with open(DEFAULT_VOICES_JSON) as f:
        return json.load(f)


def generate_one(
    *,
    client,
    job: AudioJob,
    voice_name: str,
    voice_config: dict,
    output_path: Path,
    model_id: str = DEFAULT_MODEL_ID,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    max_retries: int = 3,
) -> tuple[bool, Optional[str]]:
    """Generate a single audio file. Returns (success, error_message)."""
    if output_path.exists():
        return True, None  # already done

    rendered = render_for_tts(job.body_md)

    voice_id = voice_config["voice_id"]
    settings = voice_config.get("settings", {})

    last_error: Optional[str] = None
    for attempt in range(max_retries):
        try:
            audio = client.text_to_speech.convert(
                text=rendered.text,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                voice_settings={
                    "stability": settings.get("stability", 0.55),
                    "similarity_boost": settings.get("similarity_boost", 0.75),
                    "style": settings.get("style", 0.15),
                    "use_speaker_boost": settings.get("use_speaker_boost", True),
                },
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                # The SDK returns either bytes or an iterator of bytes
                if hasattr(audio, "__iter__") and not isinstance(audio, (bytes, bytearray)):
                    for chunk in audio:
                        f.write(chunk)
                else:
                    f.write(audio)
            return True, None
        except Exception as e:  # noqa: BLE001 - intentionally broad
            last_error = f"{type(e).__name__}: {e}"
            if attempt < max_retries - 1:
                # Exponential backoff
                wait = 2 ** attempt
                print(f"   ↻ retry in {wait}s ({last_error})")
                time.sleep(wait)
    return False, last_error


def generate_jobs(
    jobs: Iterable[AudioJob],
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    voices: Optional[list[str]] = None,
    model_id: str = DEFAULT_MODEL_ID,
    api_key: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Generate audio for all jobs in both Adam and Bella voices (or just `voices`).

    Returns a summary dict: {generated, skipped, failed, total_chars, errors}."""

    output_dir = Path(output_dir)
    voices_config = load_voices()
    voice_names = voices or list(voices_config["voices"].keys())

    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key and not dry_run:
        raise RuntimeError(
            "ELEVENLABS_API_KEY not set. Either export it, put it in .env, "
            "or pass api_key='...' explicitly."
        )

    if not dry_run:
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError as e:
            raise RuntimeError(
                "elevenlabs SDK not installed. Run: pip install elevenlabs"
            ) from e
        client = ElevenLabs(api_key=api_key)
    else:
        client = None

    summary = {
        "generated": 0,
        "skipped": 0,
        "failed": 0,
        "total_chars": 0,
        "errors": [],
    }

    jobs_list = list(jobs)
    print(f"Generating {len(jobs_list)} sessions × {len(voice_names)} voices = "
          f"{len(jobs_list) * len(voice_names)} files")
    print(f"Output: {output_dir}")
    print(f"Model:  {model_id}")
    if dry_run:
        print("DRY RUN — no API calls will be made.\n")

    for i, job in enumerate(jobs_list, start=1):
        for voice_name in voice_names:
            voice_config = voices_config["voices"][voice_name]
            output_path = output_dir / job.audio_filename(voice_name)
            tag = f"[{i}/{len(jobs_list)}] {job.audio_filename(voice_name)}"

            if output_path.exists():
                print(f"  ✓ {tag}  (already generated)")
                summary["skipped"] += 1
                continue

            if dry_run:
                rendered = render_for_tts(job.body_md)
                summary["total_chars"] += rendered.char_count
                print(f"  ○ {tag}  ({rendered.char_count} chars, would generate)")
                continue

            print(f"  → {tag}")
            success, error = generate_one(
                client=client,
                job=job,
                voice_name=voice_name,
                voice_config=voice_config,
                output_path=output_path,
                model_id=model_id,
            )
            if success:
                summary["generated"] += 1
            else:
                summary["failed"] += 1
                summary["errors"].append((str(output_path.name), error))
                print(f"  ✗ {tag}  FAILED: {error}")

            time.sleep(DELAY_BETWEEN_CALLS)

    # Summary
    print()
    print(f"Generated: {summary['generated']}")
    print(f"Skipped:   {summary['skipped']} (already existed)")
    print(f"Failed:    {summary['failed']}")
    if summary["errors"]:
        print("\nErrors:")
        for filename, err in summary["errors"]:
            print(f"  - {filename}: {err}")

    return summary


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from .parser import parse_content_dir

    content_dir = Path(__file__).resolve().parent.parent / "content"
    all_jobs = parse_content_dir(content_dir)

    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    if "--all" in args:
        jobs_to_run = all_jobs
        print(f"FULL PRODUCTION RUN: {len(all_jobs)} sessions")
    else:
        # Default: just Variant A week 1 (the pilot)
        jobs_to_run = [j for j in all_jobs if j.variant == "a" and j.week == 1]
        print(f"PILOT RUN: Variant A week 1 ({len(jobs_to_run)} sessions)")
        print("Pass --all to generate the full library, --dry-run to skip API calls.\n")

    generate_jobs(jobs_to_run, dry_run=dry_run)
